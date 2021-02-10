from bs4 import BeautifulSoup
import urllib.request
import csv
import argparse

def religion_scrap(religion, annee_depart, annee_fin):
	# query the website and return the html to the variable 'page'
	i = annee_depart

	with open(f'data/fetes_{religion}.csv', 'w', newline='') as religion_file:
		religion_writer = csv.writer(religion_file, delimiter=',')

		while i < annee_fin:
			# specify the url
			nbr = str(i)
			urlpage = 'https://www.calendrier-des-religions.ch/fetes.php?y=' + nbr + '&t=2'

			# query the website and return the html to the variable 'page'
			page = urllib.request.urlopen(urlpage)

			# parse the html using beautiful soup and store in variable 'soup'
			soup = BeautifulSoup(page, 'html.parser')
			month_year = ''
			for result in soup.find_all('section'):
				month_year = result.h2.text
				for result2 in result.find_all('article', {"class": "item_liste"}):
					row = [result2.find('div', {"class": "jour"}).text, month_year, religion,
								result2.find('div', {"class": "nom"}).text,
								result2.find('div', {"class": "description"}).text,
								result2.find('div', {"class": "note"}).text]
					row = [s.replace('\x92', "'") for s in row]
					row = [s.replace('\x96', " ") for s in row]
					row = [s.replace('\x9c', " ") for s in row]
					row = [s.strip('\xa0') for s in row]
					row = [s.strip('* ') for s in row]
					religion_writer.writerow(row)
			i += 1

if __name__ == "__main__":

	parser = argparse.ArgumentParser()

	parser.add_argument("--religion",
						help="la religion pour laquelle nous voulons les fêtes caractéristiques",
						default="chretien",
						type=str)

	parser.add_argument("--annee_depart",
						help="année de départ",
						default= 2011,
						type=int)
	parser.add_argument("--annee_fin",
						help="année de fin",
						default= 2021,
						type=float)

	args = parser.parse_args()

	religion_scrap(args.religion, args.annee_depart, args.annee_fin)