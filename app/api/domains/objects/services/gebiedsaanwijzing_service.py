from bs4 import BeautifulSoup


class GebiedsaanwijzingService:
    def get_aanwijzing_codes_in_html(self, html: str) -> set[str]:
        result: set[str] = set()

        try:
            soup: BeautifulSoup = BeautifulSoup(html, "html.parser")
            for aanwijzing_html in soup.select('a[data-hint-type="gebiedsaanwijzing"]'):
                aanwijzing_code: str = str(aanwijzing_html.get("data-code", ""))
                if not aanwijzing_code:
                    continue
                result.add(aanwijzing_code)
        except TypeError:
            pass

        return result
