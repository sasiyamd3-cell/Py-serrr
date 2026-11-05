from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import json
import requests
from bs4 import BeautifulSoup

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # URL එකේ තියෙන query parameters ලබා ගැනීම
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)
        
        movie_url = query_params.get('url', [None])[0]

        if not movie_url or 'baiscopes.lk' not in movie_url:
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response_data = {"success": False, "message": "Please provide a valid Baiscopes URL!"}
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
            return

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Referer': 'https://baiscopes.lk/'
        }

        try:
            # 1. මූවි පේජ් එකට රික්වෙස්ට් එකක් යැවීම (Analyze HTML)
            response = requests.get(movie_url, headers=headers, timeout=30)
            if response.status_code != 200:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "message": "Failed to load movie page."}).encode('utf-8'))
                return

            # 2. BeautifulSoup මඟින් HTML පාර්ස් කිරීම
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # මූවි නම ලබා ගැනීම
            title_tag = soup.find('h1', class_='entry-title') or soup.find('h1')
            movie_title = title_tag.text.strip() if title_tag else "Baiscopes Movie"

            # 3. ඩවුන්ලෝඩ් ලින්ක්ස් Deep Analyze කිරීම
            download_links = []
            for a in soup.find_all('a', href=True):
                href = a['href']
                text = a.text.strip().lower()
                
                if any(k in href for k in ['links/', 'download', 'dl.', 'mega.nz', 'pixeldrain']) or \
                   any(k in text for k in ['download', 'torrent', 'direct']):
                    download_links.append({
                        "title": a.text.strip() or "Download Link",
                        "url": href
                    })

            if not download_links:
                self.send_response(404)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "message": "No download links found."}).encode('utf-8'))
                return

            primary_link = download_links[0]['url']

            # ප්‍රතිඵලය JSON ලෙස යැවීම
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            result_data = {
                "success": True,
                "result": {
                    "ok": True,
                    "title": movie_title,
                    "downloadUrl": primary_link,
                    "allAnalyzedLinks": download_links,
                    "moviePageUrl": movie_url
                }
            }
            self.wfile.write(json.dumps(result_data).encode('utf-8'))

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"success": False, "message": str(e)}).encode('utf-8'))
