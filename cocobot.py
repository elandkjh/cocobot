import openai
import torch
import clip
import csv
from PIL import Image
import requests
from io import BytesIO

# OpenAI API 키 설정
openai.api_key = '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'

# CLIP 모델 로드
device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)

def load_data(file_paths):
    data = []
    for file_path in file_paths:
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                data.append((row['user_input'], row['response']))
    return data

def recognize_image(image_path):
    # 이미지 로드 및 전처리
    image = Image.open(image_path)
    image_input = preprocess(image).unsqueeze(0).to(device)

    # 텍스트 설명 목록
    text_descriptions = ["a banana", "an apple", "a strawberry", "a dog", "a cat", "a car", "a house", "a tree", "a book", "a laptop"]
    text_inputs = torch.cat([clip.tokenize(desc) for desc in text_descriptions]).to(device)

    # 이미지와 텍스트 비교
    with torch.no_grad():
        image_features = model.encode_image(image_input)
        text_features = model.encode_text(text_inputs)
        logits_per_image, logits_per_text = model(image_input, text_inputs)
        probs = logits_per_image.softmax(dim=-1).cpu().numpy()

    # 가장 유사한 설명 선택
    max_prob_index = probs.argmax()
    return text_descriptions[max_prob_index]

def generate_response(data, user_input, image_description=None):
    if image_description:
        user_input = f"User uploaded an image of {image_description}. Respond appropriately as Cocomong."
    
    # CSV 데이터에서 응답 찾기
    for user_query, response in data:
        if user_input.lower() in user_query.lower():
            return response
    
    # GPT-4-turbo 모델 사용
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "You are Cocomong, a cheerful and adventurous red monkey from the land of fruits. Speak and think like Cocomong."},
            {"role": "user", "content": user_input}
        ]
    )
    return response.choices[0].message['content'].strip()

# 데이터 로드
data_files = ['cocobot_data.csv', 'cocobot_conversations.csv']
data = load_data(data_files)

# 사용자와의 대화 시작
print("코코몽과 대화를 시작합니다. 이미지를 업로드하거나 종료하려면 '종료'라고 입력하세요.")

while True:
    user_input = input("사용자: ")
    
    if user_input.lower() == '종료':
        print("대화를 종료합니다.")
        break
    
    if user_input.lower() == '이미지 업로드':
        image_path = input("이미지 파일 경로를 입력하세요: ")
        image_description = recognize_image(image_path)
        response = generate_response(data, user_input, image_description)
    else:
        response = generate_response(data, user_input)
    
    print("코코몽:", response)
