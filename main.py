import logging
from dotenv import load_dotenv

from generator import BannerGenerator, GptBannerGenerator, BannerGeneratorWithText
from motleycrew.common.logging import logger, configure_logging
from motleycache import enable_cache, disable_cache

logger.setLevel(logging.INFO)
logging.getLogger().setLevel(logging.INFO)


def main():
    image_description = """Generate a high-quality image of a green bus and a pink train with text advertising a 
    bank promotion in Russian. The background should be bright orange and purple colors."""
    slogan = '''"Альфа пятница Кэшбэк 100%"'''

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
