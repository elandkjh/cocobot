import pandas as pd
import torch
from torchvision import models, transforms
from PIL import Image
import openai

# OpenAI API 키 설정
openai.api_key = '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'

# 말투 데이터 로드
conversations_df = pd.read_csv('c:/cocobot/my_flask_app/cocobot_conversations.csv')

def load_data(file_paths):
    data = []
    for file_path in file_paths:
        df = pd.read_csv(file_path, delimiter='|')
        for index, row in df.iterrows():
            keyword = str(row['keyword']).strip() if not pd.isna(row['keyword']) else ''
            response = str(row['response']).strip() if not pd.isna(row['response']) else ''
            if keyword and response:
                data.append((keyword, response))
    return data

data_files = ['c:/cocobot/my_flask_app/cocobot_data.csv']  # 데이터 파일 리스트
data = load_data(data_files)

def get_tone(user_input):
    for index, row in conversations_df.iterrows():
        if row['user_input'].strip().lower() == user_input.strip().lower():
            return row['tone']
    # 기본 말투 설정
    return "20대 초반 대학생의 친절하고 다정한 말투로 '~몽'으로 끝나는 말투를 사용해줘."

def get_response(user_input, conversation_history):
    # 데이터에서 적절한 정보를 찾습니다.
    relevant_data = ""
    for keyword, response in data:
        if keyword.lower() in user_input.lower():
            relevant_data += f"{keyword}: {response}\n"

    tone = get_tone(user_input)

    if relevant_data:
        # 키워드에 맞는 응답을 찾은 경우
        prompt = f"사용자가 '{user_input}'라고 물어봤어. 다음은 코코몽의 관련 정보야:\n{relevant_data}\n\nTone: {tone}\nCharacter: 코코몽\nConversation history: {conversation_history}"
    else:
        # 키워드에 맞는 응답을 찾지 못한 경우 일반적인 대화를 위한 프롬프트
        prompt = f"사용자가 '{user_input}'라고 물어봤어. 코코몽으로서 일반적인 대화를 이어가줘.\n\nTone: {tone}\nCharacter: 코코몽\nConversation history: {conversation_history}"

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are answering as the character 코코몽. 너의 대답이 항상 일관된 말투를 유지해야 해. 그리고 이전 대화 내용을 기억해."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200
        )
        return response.choices[0].message['content'].strip()
    except openai.error.OpenAIError as e:
        print(f"OpenAI API error: {e}")
        return "문제가 생겼어! 잠시만 쉬고 올께! 곧 다시 만나!"
    except Exception as e:
        print(f"General error: {e}")
        return "문제가 생겼어! 확인해볼게 다음에 만나!"

def recognize_image(image):
    # 이미지 인식 모델 로드 (CUDA 사용)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = models.resnet18(pretrained=True).to(device)
    model.eval()

    # 이미지 전처리
    preprocess = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    img = Image.open(image)
    img_t = preprocess(img)
    batch_t = torch.unsqueeze(img_t, 0).to(device)

    # 예측 수행
    with torch.no_grad():
        out = model(batch_t)
    
    _, index = torch.max(out, 1)
    return f"Predicted class: {index[0].item()}"
