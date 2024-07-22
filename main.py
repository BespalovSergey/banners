import logging
from dotenv import load_dotenv

from generator import BannerGenerator, GptBannerGenerator, BannerGeneratorWithText
from motleycrew.common.logging import logger, configure_logging
from motleycache import enable_cache, disable_cache

logger.setLevel(logging.INFO)
# logging.getLogger().setLevel(logging.INFO)


def main():
    image_description = """ В центре изображения находится фотография современного многоэтажного жилого здания, котороe  
     является новостройкой. Здание имеет сложную архитектурную форму с большими окнами и балконами. 
     Оно выполнено в бежево-коричневых тонах с вкраплениями серого цвета. 
     На фоне здания изображено голубое небо с белыми облаками. 
"""
    slogan = '''"Живите где хотите с гибким поиском по новостройкам"'''

    images_dir = "banner_images"
    text_description = "текст расположен в одном блоке"

    banner_generator = BannerGeneratorWithText(image_description, text_description, images_dir, slogan)
    # banner_generator = GptBannerGenerator(image_description, images_dir, slogan)
    banner_generator.run()


if __name__ == "__main__":
    configure_logging(verbose=True)
    enable_cache()
    load_dotenv()
    main()
    disable_cache()
