from flask import Flask, request, Response, jsonify
import requests
import json
import threading
import time
import queue
import yaml

app = Flask(__name__)

# 加载配置文件
with open('config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

API_BEARER_TOKEN = config.get('api_bearer_token')
MODEL_PROVIDER_API_KEY = config.get('model_provider_api_key')
DEFAULT_API_URL = config.get('default_api_url')
DEFAULT_MODEL = config.get('default_model')
STREAM_STATUS_FEEDBACK = config.get('stream_status_feedback', True)
USE_REGEX_PROCESSING = config.get('use_regex_processing', True)

def verify_token(token):
    return token == API_BEARER_TOKEN

def make_api_call(messages, max_tokens, is_final_answer=False):
    for attempt in range(3):
        try:
            data = {
                "model": DEFAULT_MODEL,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": 0.2,
                "response_format": {"type": "json_object"}
            }
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {MODEL_PROVIDER_API_KEY}"
            }
            response = requests.post(DEFAULT_API_URL, headers=headers, json=data)
            response.raise_for_status()
            return json.loads(response.json()['choices'][0]['message']['content'])
        except Exception as e:
            if attempt == 2:
                if is_final_answer:
                    return {"title": "错误", "content": f"3次尝试后无法生成最终答案。错误: {str(e)}"}
                else:
                    return {"title": "错误", "content": f"3次尝试后无法生成步骤。错误: {str(e)}", "next_action": "final_answer"}
            time.sleep(1)  # 重试前等待1秒

def generate_response(prompt):
    messages = [
        {"role": "system", "content": """You are an expert AI assistant that explains your reasoning step by step. For each step, provide a title that describes what you're doing in that step, along with the content. Decide if you need another step or if you're ready to give the final answer. Respond in JSON format with 'title', 'content', and 'next_action' (either 'continue' or 'final_answer') keys. USE AS MANY REASONING STEPS AS POSSIBLE. AT LEAST 3. BE AWARE OF YOUR LIMITATIONS AS AN LLM AND WHAT YOU CAN AND CANNOT DO. IN YOUR REASONING, INCLUDE EXPLORATION OF ALTERNATIVE ANSWERS. CONSIDER YOU MAY BE WRONG, AND IF YOU ARE WRONG IN YOUR REASONING, WHERE IT WOULD BE. FULLY TEST ALL OTHER POSSIBILITIES. YOU CAN BE WRONG. WHEN YOU SAY YOU ARE RE-EXAMINING, ACTUALLY RE-EXAMINE, AND USE ANOTHER APPROACH TO DO SO. DO NOT JUST SAY YOU ARE RE-EXAMINING. USE AT LEAST 3 METHODS TO DERIVE THE ANSWER. USE BEST PRACTICES.

Example of a valid JSON response:```json
{
    "title": "Identifying Key Information",
    "content": "To begin solving this problem, we need to carefully examine the given information and identify the crucial elements that will guide our solution process. This involves...",
    "next_action": "continue"
}```
"""},
        {"role": "user", "content": prompt},
        {"role": "assistant", "content": "Thank you! I will now think step by step following my instructions, starting at the beginning after decomposing the problem."}
    ]
    
    steps = []
    step_count = 1
    total_thinking_time = 0
    
    while True:
        start_time = time.time()
        step_data = make_api_call(messages, 300)
        end_time = time.time()
        thinking_time = end_time - start_time
        total_thinking_time += thinking_time
        
        steps.append((f"Step {step_count}: {step_data['title']}", step_data['content'], thinking_time))
        
        messages.append({"role": "assistant", "content": json.dumps(step_data)})
        
        if step_data['next_action'] == 'final_answer' or step_count > 25: # Maximum of 25 steps to prevent infinite thinking time. Can be adjusted.
            break
        
        step_count += 1

        yield steps, None  # We're not yielding the total time until the end

    # Generate final answer
    messages.append({"role": "user", "content": "Please provide the final answer based on your reasoning above."})
    
    start_time = time.time()
    final_data = make_api_call(messages, 200, is_final_answer=True)
    end_time = time.time()
    thinking_time = end_time - start_time
    total_thinking_time += thinking_time
    
    steps.append(("Final Answer", final_data['content'], thinking_time))

    yield steps, total_thinking_time

@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    # 验证 bearer token
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "未提供有效的 bearer token"}), 401
    
    token = auth_header.split(' ')[1]
    if not verify_token(token):
        return jsonify({"error": "无效的 bearer token"}), 401

    data = request.json
    messages = data['messages']
    stream = data.get('stream', False)
    
    if stream:
        def generate():
            yield 'data: {"choices":[{"delta":{"content":" "},"index":0}]}\n\n'
            
            sent_steps = set()  # 用于跟踪已发送的步骤
            
            for steps, total_thinking_time in generate_response(messages[-1]['content']):
                for i, (title, content, thinking_time) in enumerate(steps):
                    step_key = f"{title}:{content[:50]}"  # 使用标题和内容的前50个字符作为唯一标识
                    if step_key not in sent_steps:
                        sent_steps.add(step_key)
                        if USE_REGEX_PROCESSING:
                            if title.startswith("Final Answer"):
                                yield f'data: {{"choices":[{{"delta":{{"content":"\\n\\n### {title}\\n{content}"}},"index":0}}]}}\n\n'
                            else:
                                yield f'data: {{"choices":[{{"delta":{{"content":"\\n\\n## {title}\\n{content}"}},"index":0}}]}}\n\n'
                        else:
                            if title.startswith("Final Answer"):
                                yield f'data: {{"choices":[{{"delta":{{"content":"### {title}\\n{content.replace("\\n", "<br>")}"}},"index":0}}]}}\n\n'
                            else:
                                yield f'data: {{"choices":[{{"delta":{{"content":"<details open>\\n<summary>{title}</summary>\\n{content.replace("\\n", "<br>")}\\n</details>"}},"index":0}}]}}\n\n'
                if total_thinking_time is not None:
                    yield f'data: {{"choices":[{{"delta":{{"content":"\\n\\n**Total thinking time: {total_thinking_time:.2f} seconds**"}},"index":0}}]}}\n\n'
            
            yield "data: [DONE]\n\n"
        
        return Response(generate(), content_type='text/event-stream')
    else:
        # 非流式输出
        for steps, total_thinking_time in generate_response(messages[-1]['content']):
            response = {"steps": steps}
            if total_thinking_time is not None:
                response["total_thinking_time"] = total_thinking_time
            return jsonify(response)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=18888)
    