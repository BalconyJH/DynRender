from loguru import logger
from os import path, getcwd
from typing import Optional
from zipfile import ZipFile


class MakeStaticFile:
    def __init__(self, data_path: Optional[str] = None) -> None:

        self.data_path: str = data_path
        self.check_cache_file()

    def check_cache_file(self) -> None:
        # 查询是否有data_path参数
        # 没有的话静态文件目录就设置在程序的运行目录
        if self.data_path is None:
            # 确定程序的运行目录的路径
            program_running_path = getcwd()
            # 当前文件所在的目录的路径
            current_dir = path.dirname(path.abspath(__file__))
            # 静态文件的路径
            static_path = path.join(program_running_path, "Static")
            # 如果不存在静态目录将自带的压缩文件解压过去
            if not path.exists(static_path):
                logger.info("未检测到static目录")
                logger.info("用户未传入data路径,将在程序运行目录创建static目录")
                logger.info("创建static目录中...")
                file = ZipFile(path.join(current_dir, "Static.zip"))
                file.extractall(program_running_path)
                logger.info("static目录创建成功")
        # 有data_path参数参数
        else:
            # 确认当前运行的文件所在的目录
            current_dir = path.dirname(path.abspath(__file__))
            # 如果data_path存在
            if path.exists(self.data_path):
                # 设置静态文件的目录
                static_path = path.join(self.data_path, "Static")
                # 如果静态文件的目录不存在就直接解压文件
                if not path.exists(static_path):
                    logger.info("未检测到static目录")
                    logger.info("使用用户传入路径创建static目录中...")
                    file = ZipFile(path.join(current_dir, "Static.zip"))
                    file.extractall(self.data_path)
                    logger.info("static目录创建成功")
