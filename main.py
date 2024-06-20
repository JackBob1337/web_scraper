import requests
from bs4 import BeautifulSoup
import pandas as pd
import string

def extract_publications(url):
    response = requests.get(url)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        
        publications = []
        
        # Znajdujemy wszystkie elementy <b> z tytułami publikacji
        title_elements = soup.find_all('b')
        
        for title_element in title_elements:
            publication_title = title_element.text.strip()
            publications.append(publication_title)
        
        return publications
    
    else:
        print(f"Błąd podczas żądania strony: {response.status_code}")
        return []

def extract_data_from_professor_page(url):
    response = requests.get(url)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        author = None
        publications = []
        
        # Wyodrębniamy ID profesora z URL-a
        professor_id = url.split('-')[-1]
        
        # Tworzymy nowy URL z parametrami from i to
        new_url = f"https://pers.uz.zgora.pl/publikacje/pracownik-{professor_id}?from=1960&to=2025"
        
        # Wyodrębniamy publikacje z nowej strony
        publications = extract_publications(new_url)
            
        # Szukamy elementu z imieniem i nazwiskiem
        h3_elements = soup.find_all('h3')
        for h3 in h3_elements:
            if 'SKEP' in h3.text:  # Sprawdzamy, czy nagłówek zawiera 'SKEP'
                name_and_title = h3.text.replace('SKEP - ', '').strip()
                if 'dr' in name_and_title:  # Sprawdzamy obecność 'dr' w tekście
                    _, full_name = name_and_title.split('dr', 1)  # Dzielimy przez 'dr'
                    author = full_name.strip()
                break
        
        # Szukamy elementu z wymaganymi informacjami o jednostce
        td_elements = soup.find_all('td', class_='font-weight-bold')
        for td in td_elements:
            if td.text.strip() == 'Jednostka':
                faculty_td = td.find_next_sibling('td')
                if faculty_td and 'Instytut Matematyki' in faculty_td.text:
                    return author, "Instytut Matematyki", publications
        
    return None, None, []

def extract_data_from_page(url):
    response = requests.get(url)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Znajdujemy wszystkie linki do stron profesorów
        table = soup.find('table', class_='table table-bordered table-striped table-hover')
        professor_links = table.find_all('a')
        
        authors = []
        faculties = []
        ids = []
        publications_list = []
        
        for professor in professor_links:
            professor_url = professor.get('href')
            full_url = professor_url if professor_url.startswith('http') else f"https://pers.uz.zgora.pl{professor_url}"
            
            # Wyodrębniamy ID profesora
            professor_id = professor_url.split('-')[-1]
            
            author, faculty, publications = extract_data_from_professor_page(full_url)
            if faculty:
                authors.append(author)
                faculties.append(faculty)
                ids.append(professor_id)
                publications_list.append(publications)
        
        return authors, faculties, ids, publications_list
    else:
        print(f"Strona jest niedostępna, kod statusu: {response.status_code}")
        return [], [], [], []

def collect_all_data(base_url):
    all_authors = []
    all_faculties = []
    all_ids = []
    all_publications = []
    
    for letter in string.ascii_uppercase:  # Używamy wielkich liter
        url = f"{base_url}{letter}"
        print(f"Zbieranie danych z {url}")
        authors, faculties, ids, publications = extract_data_from_page(url)
        
        all_authors.extend(authors)
        all_faculties.extend(faculties)
        all_ids.extend(ids)
        all_publications.extend(publications)
    
    data = {
        'Autor': all_authors,
        'Wydział': all_faculties,
        'Numer': all_ids,
        'Publikacje': all_publications
    }
    df = pd.DataFrame(data)
    df.to_csv('publications.csv', index=False, encoding='utf-8') 
    return df

base_url = 'https://pers.uz.zgora.pl/publikacje-osoby/'
df = collect_all_data(base_url)

df.head()
