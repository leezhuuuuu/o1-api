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

# 用于存储对话历史的字典
conversation_history = {}

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
                    return {"title": "Error", "content": f"Unable to generate final answer after 3 attempts. Error: {str(e)}"}
                else:
                    return {"title": "Error", "content": f"Unable to generate step after 3 attempts. Error: {str(e)}", "next_action": "final_answer"}
            time.sleep(1)  # 重试前等待1秒

def generate_response(messages):
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
        
        if step_data['next_action'] == 'final_answer' or step_count > 25:
            break
        
        step_count += 1

        yield steps, None

    messages.append({"role": "user", "content": "Please provide the final answer based on the above reasoning."})
    
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
        return jsonify({"error": "No valid bearer token provided"}), 401
    
    token = auth_header.split(' ')[1]
    if not verify_token(token):
        return jsonify({"error": "Invalid bearer token"}), 401

    data = request.json
    conversation_id = data.get('conversation_id', 'default')
    new_message = data['messages'][-1]['content']
    stream = data.get('stream', False)
    
    # 获取或创建对话历史
    if conversation_id not in conversation_history:
        conversation_history[conversation_id] = [
            {"role": "system", "content": """You are an expert AI assistant who explains your reasoning process step by step. For each step, provide a title describing what you're doing in that step, and the content. Determine whether another step is needed or if you're ready to give a final answer. Respond in JSON format with 'title', 'content', and 'next_action' (which can be 'continue' or 'final_answer') keys. Use multiple reasoning steps whenever possible, at least 3. Be aware of your limitations as an LLM and what you can and cannot do. In your reasoning, include exploration of alternative answers. Consider that you might be wrong and where errors in your reasoning might occur. Thoroughly test all other possibilities. You may be wrong. When you say you're revisiting, actually revisit and use a different method to do so. Don't just say you're revisiting. Use at least 3 methods to arrive at an answer. Use best practices.

Example of a valid JSON response:```json
{
    "title": "Identifying Key Information",
    "content": "To begin solving this problem, we need to carefully examine the given information and identify the key elements that will guide our solution process. This involves...",
    "next_action": "continue"
}```
"""},
        ]
    
    # 添加新消息到历史
    conversation_history[conversation_id].append({"role": "user", "content": new_message})
    
    if stream:
        def generate():
            yield 'data: {"choices":[{"delta":{"content":" "},"index":0}]}\n\n'
            
            sent_steps = set()
            
            for steps, total_thinking_time in generate_response(conversation_history[conversation_id]):
                for i, (title, content, thinking_time) in enumerate(steps):
                    step_key = f"{title}:{content[:50]}"
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
            
            # 将AI响应添加到历史
            conversation_history[conversation_id].append({"role": "assistant", "content": steps[-1][1]})
            
            yield "data: [DONE]\n\n"
        
        return Response(generate(), content_type='text/event-stream')
    else:
        # 非流式输出
        response = {"steps": []}
        for steps, total_thinking_time in generate_response(conversation_history[conversation_id]):
            response["steps"] = steps
            if total_thinking_time is not None:
                response["total_thinking_time"] = total_thinking_time
        
        # 将AI响应添加到历史
        conversation_history[conversation_id].append({"role": "assistant", "content": steps[-1][1]})
        
        return jsonify(response)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=18888)