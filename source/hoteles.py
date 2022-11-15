"""
OBJETIVO:
    - Extraer información sobre hoteles en Chicago y Atlanta.
    - Scrolling horizontal y vertical con reglas.
    - MapCompose para realizar limpieza de datos
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
class Hotel(Item):
    nombre = Field()
    ciudad = Field()
    descripcion = Field()
    amenities = Field()
    valoracion = Field()
    direccion = Field()
    precio = Field()


# Definimos el CrawlSpider
class TripAdvisor(CrawlSpider):
    name = 'hotels'
    custom_settings = {  # Definimos un USER_AGENT para no ser baneados.
        'USER_AGENT': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36"}  # Número máximo de páginas a scrapear

    allowed_domains = ['tripadvisor.com']  # la búsqueda se reduce al dominio.
    start_urls = ['https://www.tripadvisor.com/Hotels-g35805-Chicago_Illinois-Hotels.html',
                  'https://www.tripadvisor.com/Hotels-g60898-Atlanta_Georgia-Hotels.html']  # url´s a scrapear

    # Tiempo de espera entre cada requerimiento. Protección IP.
    download_delay = 5

    # Reglas para direccionar el movimiento del Crawler a través de las páginas.
    rules = (
        # SCROLLING HORIZONTAL: paginación de hoteles:
        Rule(
            LinkExtractor(
                allow=r'-oa\d+-'  # regex para paginar correctamente.
            ), follow=True
        ),
        # SCROLLING VERTICAL: detalle de los hoteles:
        Rule(
            LinkExtractor(
                allow=r'/Hotel_Review-',  # Regex para hacer requerimiento si hay coincidencia.
                restrict_xpaths=[
                    '//div[@id="taplc_hsx_hotel_list_lite_dusty_hotels_combined_sponsored_undated_0"]//a[@data-clicksource="HotelName"]']
                # Evita duplicados.

            ), follow=True, callback="parse_hotel"
        )
    )

    # Callback de la regla
    def parse_hotel(self, response):
        sel = Selector(response)
        item = ItemLoader(Hotel(), sel)
        item.add_xpath('nombre', '//h1[@id="HEADING"]/text()')
        item.add_xpath('ciudad', '//*[@id="taplc_trip_planner_breadcrumbs_0"]/ul/li[3]/a/span/text()')
        item.add_xpath('descripcion',
                       '//*[@id="taplc_about_with_photos_react_0"]/div/div/div/div/div[2]/div/div[3]/div/div/text()',
                       MapCompose(lambda i: i.replace('\n', '').replace('\r', '')))
        item.add_xpath('amenities', '//div[contains(@data-test-target, "amenity_text")]/text()')
        item.add_xpath('valoracion', '//*[@id="ABOUT_TAB"]/div[2]/div[1]/div[1]/span/text()')
        item.add_xpath('direccion',
                       '/html/body/div[2]/div[2]/div[2]/div[6]/div/div/div/div/div/div[4]/div[1]/div[2]/span[2]/span/text()')
        item.add_xpath('precio',
                       '/html/body/div[2]/div[2]/div[1]/div[1]/div[2]/div[1]/div/div[6]/div/div/div[1]/div[1]/div/div[2]/div/div/text()')

        yield item.load_item()

# EJECUCIÓN
# scrapy runspider hoteles.py -o df_hoteles.csv -t csv
