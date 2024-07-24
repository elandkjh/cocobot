# Git 설치 확인
if ! command -v git &> /dev/null
then
    echo "git could not be found. Please install git first."
    exit
fi

# clip 라이브러리 설치
git clone https://github.com/openai/CLIP.git
cd CLIP
pip install -e .
cd ..
