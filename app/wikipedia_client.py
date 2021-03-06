import requests
import logging
from app.params import params


class GPSCoordinatesError(Exception):
    """
   This class inherits from the Exception class. It is used to throw a particular exception and
   make it cause an error message to be drawn in the return dict.
    """
    pass


class WikiClient:
    """
    This class allows Wikipedia articles to be searched using two methods using GPS coordinates extract to GoogleClient class.
    """

    def __init__(self):
        """
        This method initializes several class parameters. The wikipedia API url that will be used made requests,
        the two parameter dictionaries to be passed for the two API calls and the preformatted result dict.
        """
        self.coordinates = None
        self._url = "https://fr.wikipedia.org/w/api.php"
        self._payload_geosearch = params['payload_geosearch']
        self._pageids = None
        self._payload_search_page = params['payload_search_page']
        self._payload_pageimages = params['payload_pageimages']
        self._payload_get_image = params['payload_get_image']
        self.result = {"title": "", "wiki_url": "", "extract": "", "error": "", "image": "no image found"}

    def is_valid(self, coords):
        """
       This method checks that the coordinates are indeed present in the dict passed in parameter
       and to reformat them in the format acceptable for the API of wikipedia.

       Args :
           coords (dict) : Dictionary from GoogleClient containing GPS coordinates

       Returns :
           dict : Dictionary containing gps coordinates formatted for the WikiPedia API

        """
        try:
            dict_coords = f"{coords['coordinates']['lat']}|{coords['coordinates']['lng']}"
        except KeyError:
            self.result["error"] = "Wrong format of gps coordinates"
            raise GPSCoordinatesError
        return dict_coords

    def _clean_searchpage(self, dict_to_clean):
        """
        Formats the return dict of the search_page method to retrieve only the information important for the rest of the program
        Args :
            dict_to_clean (dict): dictionary from the request to the wikipedia API

        Returns:
            dict : Returns a cleaned dictionary of unnecessary information
        """
        self.result = {"title": dict_to_clean["query"]["pages"][str(self._pageids)]["title"],
                       "wiki_url": dict_to_clean["query"]["pages"][str(self._pageids)]["fullurl"],
                       "extract": dict_to_clean["query"]["pages"][str(self._pageids)]["extract"],
                       "image": "no image found",
                       "error": ""}
        return self.result

    def _geosearch(self, coords):
        """
        _geosearch  makes the first request to Wikipedia. This query searches for items based
        GPS coordinates passed as parameters. The API returns a list of articles with their id.
        We get here the first id of the article which is closest to the gps points.
        Args :
            coords (dict): coordinates dictionary passed to is_valide method

        Returns:
            dict : The article id corresponding to the article closest to the place indicated
        """
        self._payload_geosearch['gscoord'] = self.is_valid(coords)
        result_requests = requests.get(self._url, params=self._payload_geosearch)
        result_json = result_requests.json()
        geo_coords = result_json["query"]["geosearch"][0]["pageid"]
        return geo_coords

    def _get_image(self):
        """
        Method not yet used which allows to recover the url of the image of the Wikipedia article.
        Returns:
            string : contains wikipedia article's url image
        """
        self._payload_pageimages['pageids'] = self._pageids
        page_images_request = requests.get(self._url, self._payload_pageimages)
        page_image_json = page_images_request.json()
        self._payload_get_image[
            "titles"] = f"Image:{page_image_json['query']['pages'][str(self._pageids)]['pageimage']}"
        url_image_request = requests.get(self._url, self._payload_get_image)
        url_image_json = url_image_request.json()
        image_id = list(url_image_json['query']['pages'].keys())[0]
        self.result['image'] = url_image_json['query']['pages'][image_id]["imageinfo"][0]["url"]

    def search_page(self, coords):
        """
        This method makes the second request to the Wikipedia API with the result of the first.
        This query searches for the article linked to the id extracted by _geosearch and
        returns useful information in a dictionary using _clean_searchpage.
        This method calls all the others.
        Args:
            coords (dict) : parameter to call the geosearch method
        Returns:
            dict : Returns a cleaned dictionary of unnecessary information
        """
        try:
            self._pageids = self._geosearch(coords)
            self._payload_search_page["pageids"] = self._pageids
            result_requests = requests.get(self._url, params=self._payload_search_page)
            result_json = result_requests.json()
            self.result = self._clean_searchpage(result_json)
        except requests.exceptions.HTTPError:
            logging.critical(
                f"There is a problem with the server HTTP - Code HTTP : %s", result_requests.status_code())
            self.result["error"] = "Problem Server"
        except (AssertionError, KeyError):
            logging.error("ERROR :: There is a problem with MediaWiki searchpage answer")
            self.result["error"] = "No result found in Wikipedia"
        except GPSCoordinatesError:
            self.result["error"] = "Wrong GPS coordinates format"
        finally:
            return self.result


if __name__ == "__main__":
    pass
