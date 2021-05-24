#This project is a web scraper, parser, and converter that scrapes data from a light novel site, 
#cleans it up, then parses it into first a string and then an Epub ebook. It currently is set up 
#for multiple authors due to the prevalence of author names being listed both in romaji and kanji.

#The targeted book is easily changed by changing the ln_url variable.





    #   ----
    #
    #   Upcoming features:
    #        -a switch that will assess the number of authors and switch between a string and list format.
    #        -a table of contents
    #        -individually added chapters for better epub structure
    #        -automatic division into volumes (not sure how this would be added. Maybe some sort of other site
    #                                         that lists how many chapters per volume. Wouldn't work for web 
    #                                         novels though, or incomplete series.)
    #       -speed up the script (possibly with concurrent processes?)
    #       -try to bold the chapter names (first <p> in each chapter)






import re
import requests
from bs4 import BeautifulSoup
import shutil
from selenium import webdriver
import ebooklib
from ebooklib import epub
import cchardet as chardet
import urllib3

driver = webdriver.Chrome(executable_path=r'C:\Users\alexi\chrome_webdriver\chromedriver.exe')



ln_url = 'https://novelupdate.org/novel/common-sense-of-a-dukes-daughter'
driver.get(ln_url)
page = driver.page_source

#   Variables

results = []
title = ()
chapter_links = []
tag_text = ()
booktitle = ()
authors = []
chapter_content = []
chapter_title = ()
ch_number = ()
book_content_string = ''



#   FUNCTIONS
#-----------------


#   Export to epub function

#def convert_markdown_to_epub(book_content_string):
#    filters = ['C:\Program Files (x86)\Microsoft Visual Studio\Shared\Python37_64\Scripts\pandoc-docx-pagebreakpy.exe']
#    docname = booktitle + '.epub'
#    output = pypandoc.convert_text(
#        book_content_string, 
#        'epub', 
#        format = 'md', 
#        outputfile= docname, 
#        filters = filters)
#    pass


#   Export to word function

#def convert_markdown_to_docx(book_content_string):
#    filters = ['C:\Program Files (x86)\Microsoft Visual Studio\Shared\Python37_64\Scripts\pandoc-docx-pagebreakpy.exe']
#    docname = booktitle + '.docx'
#    output = pypandoc.convert_text(
#        book_content_string, 
#        'docx', 
#        format = 'md', 
#        outputfile= docname, 
#        filters = filters)
#    pass


#   Takes full book string and creates a structured and formatted html document out of it

def wrapStringInHTMLWindows(booktitle, body):
    import datetime
    from webbrowser import open_new_tab

    now = datetime.datetime.today().strftime("%Y%m%d-%H%M%S")

    filename = booktitle + '.html'
    f = open(filename,'w', encoding= 'utf-8')

    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
    <title>
    <h1>
    %s
    </h1>
    </title>
    </head>
    <body>

    %s

    </body>
    </html>
    """

    whole = html_content % (booktitle, body)
    f.write(whole)
    f.close()

    open_new_tab(filename)
    return filename


#   Per-Book tasks (title, author, and listing chapter links)

#   load the pagesource into BS class, that analyzes the HTML as a nested data structure and allows us to target data with selectors

soup = BeautifulSoup(page, 'html.parser')


#   eliminate the unnecessary in-line styling

for tag in soup():
    for attribute in ["style"]:
        del tag[attribute]


#   scrape title

for item in soup.findAll(attrs = {'class': 'novel-desc'}):
    booktitle = item.find('h1').text
    formatted_name = '<h1><b>' + booktitle + '</h1></b>'

    
#   scrape cover img

book_div = soup.find(attrs = {'class': 'book'})
book_cover_img_tag = book_div.find('img')
book_cover_link = book_cover_img_tag.attrs['src']
cover_filename = 'cover.jpg'


#   parse and create cover img file

r = requests.get(book_cover_link, stream=True)
if r.status_code == 200:
    with open(cover_filename, 'wb') as f:
        r.raw.decode_content = True
        shutil.copyfileobj(r.raw, f)


#   scrape and parse authors and store in a list

for div in soup.find_all('div',{'class':'info'}):
    a = div.find_all('a')
    for link in a:
        href = link.get('href')

        if href.startswith('/author/'):
            authorname = link.text
            authors.append(authorname) 
            print('authorname = ' + authorname)
        else:
            pass


#   scrape and parse novel summary and remove double spaces that occurred for some reason

novel_summary = soup.find(attrs = {'class': 'summary'}).text
summary_list = novel_summary.split()
novel_summary = ' '.join(summary_list)


#   format summary

formatted_summary = '<i>' + novel_summary + '</i>' + '<br><br><br><br>'



#   add Keywords (genre etc)

#book_content_string += "keywords: "

#for div in soup.find_all('div',{'class':'info'}):
#    a = div.find_all('a')
#    for link in a:
#        href = link.get('href')
#        if href.startswith('/genre/'):
#            keywordname = link.text
#            book_content_string += keywordname + ', '
#        else:
#            pass
#book_content_string += '<br><br>'


#   add title, image, and summary to markdown string

book_content_string += formatted_name
book_content_string += '<img alt="' + booktitle + '" src="' + cover_filename + '"></img><br><br>'
book_content_string += formatted_summary + '<br><br>'


#   scrape all divs with class chapter-list

div_chapter_list = soup.find_all(attrs = {'class': 'chapter-list'})



#   scrape and parse list of chapter links

for item in div_chapter_list:
    y = item.findAll(attrs = {'role': 'list'})
    for item in y:
        x = item.findAll('a')
        for item in x:
            url = item.get('href')
            link = 'https://novelupdate.org' + url
            chapter_links.append(link)



#   puts list in ascending order since site lists in descending order

chapter_links.reverse()


#iterate through chapters and pull all text excluding repeating advertisements or requests to report errors

for item in chapter_links:

    #   pull each chapter url and parse

    chapter_page = driver.get(item)
    ch_page = driver.page_source
    chapter_soup = BeautifulSoup(ch_page, 'html.parser')


    #   eliminates all inline styles in the parsed html

    for tag in chapter_soup():
        for attribute in ["style"]:
            del tag[attribute]
    

    #   pull and print title of each chapter

    class_chapterinfo = chapter_soup.findAll(attrs = {'class': 'chapter-info'})
    for item in class_chapterinfo:
        chapter_title = item.find('h3').text
        formatted_chapter_title = '<h2><b>' + chapter_title + '</b></h2>'
        book_content_string += formatted_chapter_title

    #   variables representing common strings to clean from the data

    advertisement = '*** You are reading on https://novelupdate.org ***'
    author_note = 'If you find any errors'

    #   parse and print chapter contents only

    chapter_content = chapter_soup.findAll(attrs = {'class': 'chapter-content'})
    for item in chapter_content:
        chap_content_list = item.find_all('p')
        for item in chap_content_list:
            p_text = item.text

            #   removing unwanted comments and advertisements

            if p_text.startswith(advertisement):
                pass
            elif p_text.startswith(author_note):
                pass
            else:
                p_tag = str(item)
                formatted_chapter_text = p_tag
                book_content_string += formatted_chapter_text 

        book_content_string += '<br><br><br><br>'


    #   for testing purposes this will prevent looping through all the chapters and spamming the site with requests

    #   break

#   Unsure if this needs to be here, as the code isn't modular yet.

if __name__ == '__main__':
    ...
    book = epub.EpubBook()


    #   set metadata

    book.set_identifier(booktitle + '123')
    book.set_title(booktitle)
    book.set_language('en')


    #book.add_author(authorname)         ---------will be used for the switch mentioned in upcoming features

    for author in authors:
        book.add_author(author)


    #   add cover file to epub
    cover_file = epub.EpubItem(uid=booktitle + 'cover',
                               file_name = cover_filename,
                               media_type = 'image/jpeg',
                               content = 'image'
                               )

    #   set cover file as cover

    cover = book.set_cover(cover_filename, open(cover_filename, 'rb').read())

        

    #   makes the book title more suitable for a filename by removing spaces and making all lowercase

    cleanbooktitle = booktitle.replace("’", '')
    cleanbooktitle = ''.join(booktitle.split()).lower()


    #   wrap content in HTML and create a .html file

    wrapStringInHTMLWindows(booktitle, book_content_string)


    #   creates filename for the inner content we scraped and formatted from the website

    content_filename = cleanbooktitle + '.html'


    #   adds in the content .html file

    content = epub.EpubHtml(title='content', file_name= content_filename, lang='en', media_type='text/html')
    content.set_content(book_content_string)
    book.add_item(content)


    #   create spine, add cover page as first page

    book.spine = ['cover', content]

    final_filename = booktitle + '.epub'
    

    #   compiles the ebook

    epub.write_epub(final_filename, book)


