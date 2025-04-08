#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import time
import os
import re
import pandas as pd
from tqdm import tqdm
import argparse
from pathlib import Path

# Sci-Hub 镜像地址列表
SCIHUB_MIRRORS = ['https://sci-hub.ru/', 'https://sci-hub.st/', 'https://sci-hub.se/']

# 设置请求头，模拟浏览器访问
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def sanitize_filename(doi):
    """清理 DOI，使其成为有效的文件名"""
    sanitized = re.sub(r'[\\/*?:"<>|]', "", doi)
    sanitized = sanitized.replace('/', '_')
    return f"{sanitized}.pdf"

def download_paper(doi, download_dir='.', mirrors=SCIHUB_MIRRORS):
    """
    尝试从 Sci-Hub 镜像下载指定 DOI 的文献。

    Args:
        doi (str): 需要下载的文献的 DOI。
        download_dir (str): 下载文件的保存目录。
        mirrors (list): Sci-Hub 镜像地址列表。

    Returns:
        bool: 下载成功返回 True，否则返回 False。
    """
    filename = sanitize_filename(doi)
    filepath = os.path.join(download_dir, filename)

    # 如果文件已存在，跳过下载
    if os.path.exists(filepath):
        return True

    # 尝试所有镜像
    for base_url in mirrors:
        try:
            # 1. 访问 Sci-Hub 页面
            query_url = f"{base_url}{doi}"
            response = requests.get(query_url, headers=HEADERS, timeout=30)
            response.raise_for_status()

            # 2. 解析 HTML 查找 PDF 链接
            soup = BeautifulSoup(response.content, 'html.parser')
            pdf_element = soup.find(id='pdf') or soup.find(id='article')

            pdf_url = None
            if pdf_element:
                if pdf_element.name in ['iframe', 'embed']:
                    pdf_url = pdf_element.get('src')
                elif pdf_element.name == 'a':
                    pdf_url = pdf_element.get('href')
                elif pdf_element.find('button', onclick=True):
                    onclick_attr = pdf_element.find('button', onclick=True)['onclick']
                    match = re.search(r"location\.href='([^']+)'", onclick_attr)
                    if match:
                        pdf_url = match.group(1)

            if not pdf_url:
                pdf_links = soup.find_all('a', href=lambda href: href and href.endswith('.pdf'))
                if len(pdf_links) == 1:
                    pdf_url = pdf_links[0]['href']
                else:
                    potential_links = soup.select('iframe[src*="//"], embed[src*="//"], a[href*="//"]')
                    for link in potential_links:
                        url = link.get('src') or link.get('href')
                        if 'pdf' in url.lower() or 'download' in url.lower():
                            pdf_url = url
                            break

            if pdf_url:
                # 3. 处理相对链接和协议问题
                if pdf_url.startswith('//'):
                    pdf_url = 'https:' + pdf_url
                elif pdf_url.startswith('/'):
                    final_base_url = response.url.split('/')[0] + '//' + response.url.split('/')[2]
                    pdf_url = final_base_url + pdf_url
                elif not pdf_url.startswith('http'):
                    current_page_url_parts = response.url.split('/')
                    pdf_url = '/'.join(current_page_url_parts[:-1]) + '/' + pdf_url

                # 4. 下载 PDF 文件
                pdf_response = requests.get(pdf_url, headers=HEADERS, stream=True, timeout=60)
                pdf_response.raise_for_status()

                os.makedirs(download_dir, exist_ok=True)

                with open(filepath, 'wb') as f:
                    for chunk in pdf_response.iter_content(chunk_size=8192):
                        f.write(chunk)
                return True

        except requests.exceptions.RequestException:
            continue
        except Exception:
            continue

        time.sleep(2)

    return False

def main():
    parser = argparse.ArgumentParser(description='Download papers from Sci-Hub using DOIs from an Excel file')
    parser.add_argument('--input', required=True, help='Path to the input Excel file')
    parser.add_argument('--output', default='./pdf', help='Directory to save downloaded PDFs')
    parser.add_argument('--delay', type=int, default=5, help='Delay between downloads in seconds')
    
    args = parser.parse_args()
    
    # 确保输入文件存在
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        return
    
    # 读取 Excel 文件
    try:
        table = pd.read_excel(input_path)
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return
    
    # 处理 DOIs
    dois_to_download = table['DOI'].copy(deep=True)
    dois_to_download = dois_to_download.dropna()
    dois_to_download = dois_to_download[dois_to_download != '']
    dois_to_download = dois_to_download.astype(str).str.strip()
    dois_to_download = dois_to_download[dois_to_download.str.match(r'^10\..+')]
    
    # 创建输出目录
    output_dir = Path(args.output)
    os.makedirs(output_dir, exist_ok=True)
    
    print("--- Starting batch download ---")
    print(f"Files will be saved to: {output_dir.absolute()}")
    print(f"Total papers to download: {len(dois_to_download)}")
    
    successful_downloads = 0
    failed_dois = []
    skipped_dois = []
    invalid_dois = []
    
    with tqdm(total=len(dois_to_download), desc="Downloading", unit="paper") as pbar:
        for doi in dois_to_download:
            doi = doi.strip()
            
            if not doi or not doi.startswith('10.'):
                invalid_dois.append(doi)
                pbar.set_postfix({
                    "Success": successful_downloads,
                    "Failed": len(failed_dois),
                    "Skipped": len(skipped_dois),
                    "Invalid": len(invalid_dois)
                })
                pbar.update(1)
                continue
            
            filename = sanitize_filename(doi)
            filepath = output_dir / filename
            
            if filepath.exists():
                skipped_dois.append(doi)
                pbar.set_postfix({
                    "Success": successful_downloads,
                    "Failed": len(failed_dois),
                    "Skipped": len(skipped_dois),
                    "Invalid": len(invalid_dois)
                })
                pbar.update(1)
                continue
            
            if download_paper(doi, download_dir=str(output_dir)):
                successful_downloads += 1
            else:
                failed_dois.append(doi)
            
            pbar.set_postfix({
                "Success": successful_downloads,
                "Failed": len(failed_dois),
                "Skipped": len(skipped_dois),
                "Invalid": len(invalid_dois)
            })
            pbar.update(1)
            
            time.sleep(args.delay)
    
    print("\n--- Download Complete ---")
    print(f"Total attempted: {len(dois_to_download)}")
    print(f"Successfully downloaded: {successful_downloads}")
    print(f"Skipped (already exists): {len(skipped_dois)}")
    print(f"Failed to download: {len(failed_dois)}")
    print(f"Invalid DOIs: {len(invalid_dois)}")
    
    if failed_dois:
        print("\nFailed DOIs:")
        for failed_doi in failed_dois:
            print(f"  - {failed_doi}")
    
    if invalid_dois:
        print("\nInvalid DOIs:")
        for invalid_doi in invalid_dois:
            print(f"  - {invalid_doi}")

if __name__ == "__main__":
    main() 