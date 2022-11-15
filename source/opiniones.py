"""
OBJETIVO:
    - Extraer información sobre opiniones de hoteles de Chicago y Atlanta.
    - Scrolling horizontal y vertical a dos niveles con reglas.
CREADO POR: Jorge Ramón Díaz Suárez y Victor Fernández Moreno

"""

from scrapy.item import Field
from scrapy.item import Item
from scrapy.spiders import CrawlSpider, Rule
from scrapy.selector import Selector
from scrapy.loader.processors import MapCompose
from scrapy.linkextractors import LinkExtractor
from scrapy.loader import ItemLoader


# Abstracción de los datos que interesan para el proyecto:
class Opinion(Item):
    titulo = Field()
    calificacion = Field()
    autor = Field()
    contenido = Field()
    hotel = Field()


# Definimos el Crawspider
class TripAdvisor(CrawlSpider):
    name = 'Opiniones'
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.117 Safari/537.36',
        'CLOSESPIDER_ITEMCOUNT':2000# Número máximo de items a scrapear
    }

    allowed_domains = ['tripadvisor.com']  # la búsqueda se reduce al dominio.
    start_urls = ['https://www.tripadvisor.com/Hotels-g35805-Chicago_Illinois-Hotels.html',
                  'https://www.tripadvisor.com/Hotels-g60898-Atlanta_Georgia-Hotels.html']  # url´s a scrapear
    # Tiempo de espera entre cada requerimiento. Protección IP.
    download_delay = 2

    # Reglas para direccionar el movimiento del Crawler a través de las páginas. Son 4 reglas una para paginar los
    # hoteles otra para ir al detalle de los hoteles, otra para la paginación de las opiniones y otra regla para ir al
    # detalle del perfil de los usuarios
    rules = (
        # SCROLLING HORIZONTAL: paginación de los hoteles
        Rule(
            LinkExtractor(
                allow=r'-oa\d+-'  # regex para paginar correctamente.
            ), follow=True
        ),
        # SCROLLING VERTICAL: detalle de los hoteles:
        Rule(
            LinkExtractor(
                allow=r'/Hotel_Review-',  # regex para paginar correctamente.
                restrict_xpaths=[
                    '//div[@id="taplc_hsx_hotel_list_lite_dusty_hotels_combined_sponsored_undated_0"]//a[@data-clicksource="HotelName"]']
                # Evita duplicados.
            ), follow=True
        ),
        # SCROLLING HORIZONTAL: Segundo nivel para la paginación de opiniones.
        Rule(
            LinkExtractor(
                allow=r'-or\d+-'
            ), follow=True
        ),
        # SCROLLING VERTICAL: Segundo nivel para el detalle de usuario.
        Rule(
            LinkExtractor(
                allow=r'/Profile/',  # regex para ir a las distintas páginas de los distintos usuarios.
                restrict_xpaths=['//div[@data-test-target="HR_CC_CARD"]//a[contains(@class,"ui_header_link uyyBf")]']
                # Evita duplicados.
            ), follow=True, callback='parse_opinion'
        )
    )
    # Abajo función para obtener la calificación.
    def obtenerCalificacion(self, texto):
        calificacion = texto.split("_")[-1]
        return calificacion

    # Callback de la regla:
    def parse_opinion(self, respose):
        sel = Selector(respose)
        opiniones = sel.xpath('//div[@id="content"]/div/div')
        autor = sel.xpath(
            '//*[@id="component_1"]/div/div[2]/div/div/div[1]/div/span[2]/span[1]/h1/span/text()').get()

        # Bucle para sacar por cada opinión los datos.

        for opinion in opiniones:
            item = ItemLoader(Opinion(), opinion)
            item.add_xpath('titulo', './/div[@class="AzIrY b _a VrCoN"]/text()')
            item.add_value('autor', autor)
            item.add_xpath('contenido', './/q/text()')
            item.add_xpath('calificacion', './/div[@class="muQub VrCoN"]/span/@class',
                           MapCompose(self.obtenerCalificacion))
            item.add_xpath('hotel', './/div[contains(@class, "ui_card section")]//div[@title]/text()')

            yield item.load_item()

# EJECUCION
# scrapy runspider opiniones.py -o df_opiniones.csv -t csv
