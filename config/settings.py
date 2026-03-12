import pathlib

import dotenv


dotenv.load_dotenv()

class Settings:
    #文件相关的
    root_dir:str = pathlib.Path(__file__).parent.parent
    upload_dir:str = 'uploads'
    file_dir:pathlib.Path = root_dir / upload_dir





settings = Settings()


if  __name__ == "__main__":
    print(settings.root_dir)
    print(settings.file_dir)
