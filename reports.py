from werkzeug.exceptions import BadRequestKeyError
from fpdf import FPDF

from flask import Flask, request, render_template, session, flash, redirect, url_for, Blueprint, Response
from loggings import isWorkerLoggedIn
from errorsAndCommunicates import noPermissions

reports = Blueprint("reports", __name__, static_folder="static", template_folder="templates")

@reports.route("/reports")
def genReports():
    from app import mysql
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT DISTINCT EXTRACT(YEAR FROM DataWyp) FROM `wypozyczenia`;')
    years = [row[0] for row in cursor.fetchall()]
    cursor.execute("SELECT * FROM `autorzy`")
    authors = [author for author in cursor.fetchall()]
    return isWorkerLoggedIn("reports.html", availableYears= years, authors= authors)


#method which convert month integer to string(Polish word)
def convertNumberToMonth(number):
        if number == 1:
            return "Styczeń"
        elif number == 2:
            return "Luty"
        elif number == 3:
            return "Marzec"
        elif number == 4:
            return "Kwiecień"
        elif number == 5:
            return "Maj"
        elif number == 6:
            return "Czerwiec"
        elif number == 7:
            return "Lipiec"
        elif number == 8:
            return "Sierpień"
        elif number == 9:
            return "Wrzesień"
        elif number == 10:
            return "Październik"
        elif number == 11:
            return "Listopad"
        elif number == 12:
            return "Grudzień"


#method which set FPDF object and another related with it attributes
def setFpdfObject(headline, columnsNumber):
    pdf = FPDF()
    pdf.add_page()
    pageWidth = pdf.w - 2*pdf.l_margin
    pdf.add_font('DejaVu', '', 'DejaVuSansCondensed.ttf', uni=True)
    pdf.set_font('DejaVu', '', 12)
    pdf.cell(pageWidth, 0.0, headline, align='C')
    pdf.ln(20)
    col_width = pageWidth/columnsNumber
    pdf.ln(1)
    th = pdf.font_size
    return pdf, col_width, th
    

@reports.route("/monthReaders", methods=['GET', 'POST'])
def monthReadersReport():
    from app import mysql
    try:
        chosenYear = request.form['chosenYear']
        cursor = mysql.connection.cursor()
        cursor.execute(f"SELECT EXTRACT(MONTH FROM w.DataWyp) AS miesiac, COUNT(DISTINCT c.IdCz) AS liczba_czytelnikow FROM `wypozyczenia` AS w INNER JOIN `czytelnicy` AS c ON w.IdCz = c.IdCz WHERE EXTRACT(YEAR FROM w.DataWyp) = %s GROUP BY EXTRACT(MONTH FROM w.DataWyp) ORDER BY EXTRACT(MONTH FROM w.DataWyp);", (chosenYear, ))
        result = cursor.fetchall()
        pdf, col_width, th = setFpdfObject(f'Liczba czytelników w danych miesiącach w roku {chosenYear}', 2)
        
        #headlines
        pdf.cell(col_width, th, "Miesiąc", border=1)
        pdf.cell(col_width, th, "Liczba czytelników", border=1)
        pdf.ln(th)
        
        for row in result:
            pdf.cell(col_width, th, convertNumberToMonth(row[0]), border=1)
            pdf.cell(col_width, th, str(row[1]), border=1)
            pdf.ln(th)
            
        cursor.close()
        return Response(pdf.output(dest='S').encode('latin-1'), mimetype='application/pdf', headers={'Content-Disposition':'attachment; filename=raport1.pdf'})
    except BadRequestKeyError:
        return noPermissions()


@reports.route("/workerBorrows", methods=['GET', 'POST'])
def workerBorrowsReport():
    from app import mysql
    try:
        chosenWorker = request.form['workerType']
        cursor = mysql.connection.cursor()
        
        if chosenWorker == 'borrower':
            workerType = "IdPWyd"
            workerName = "wypożyczający"
        else:
            workerType = 'IdPOdb'
            workerName = "odbierający"
            
        cursor.execute(f"SELECT w.IdP AS id_pracownika, w.NazwiskoP AS nazwisko_pracownika, w.ImieP AS imie_pracownika, COUNT(b.{workerType}) AS liczba_wypozyczen FROM `pracownicy` w LEFT JOIN `wypozyczenia` b ON b.{workerType} = w.IdP GROUP BY w.IdP, w.NazwiskoP ORDER BY w.IdP;")
        result = cursor.fetchall() 
        pdf, col_width, th = setFpdfObject(f'Liczba wystąpień każdego pracownika w wypożyczeniach jako {workerName}', 4)
        
        #headlines
        pdf.cell(col_width, th, "ID pracownika", border=1)
        pdf.cell(col_width, th, "Nazwisko pracownika", border=1)
        pdf.cell(col_width, th, "Imię pracownika", border=1)
        pdf.cell(col_width, th, "Liczba wypożyczeń", border=1)
        pdf.ln(th)
        
        for row in result:
            pdf.cell(col_width, th, str(row[0]), border=1)
            pdf.cell(col_width, th, row[1], border=1)
            pdf.cell(col_width, th, row[2], border=1)
            pdf.cell(col_width, th, str(row[3]), border=1)
            pdf.ln(th)
            
        cursor.close()
        return Response(pdf.output(dest='S').encode('latin-1'), mimetype='application/pdf', headers={'Content-Disposition':'attachment; filename=raport2.pdf'})
    except BadRequestKeyError:
        return noPermissions()



@reports.route("/authorBooks", methods=['GET', 'POST'])
def authorBooksReport():
    from app import mysql
    try:
        chosenAuthor = request.form['allAuthors']
        splittedAuthor = chosenAuthor.strip('()').split(', ')
        splittedAuthor = [author.replace("'", "") for author in splittedAuthor]
        tupleAuthor = tuple(splittedAuthor)
        cursor = mysql.connection.cursor()
        cursor.execute(f"SELECT k.Tytul, k.LiczDostEgz FROM ksiazki k JOIN autorstwa a ON k.ISBN = a.ISBN JOIN autorzy aut ON a.IdA = aut.IdA WHERE aut.IdA = %s;", (str(tupleAuthor[0]), ))
        result = cursor.fetchall()
        pdf, col_width, th = setFpdfObject(f'Książki autora {tupleAuthor[1]} {tupleAuthor[2]} dostępne w bibliotece w podanej liczbie egzemplarzy', 2)
        
        #headlines
        pdf.cell(col_width, th, "Tytuł książki", border=1)
        pdf.cell(col_width, th, "Dostępne egzemplarze", border=1)
        pdf.ln(th)
        
        for row in result:
            pdf.cell(col_width, th, row[0], border=1)
            pdf.cell(col_width, th, str(row[1]), border=1)
            pdf.ln(th) 
            
        cursor.close()
        return Response(pdf.output(dest='S').encode('latin-1'), mimetype='application/pdf', headers={'Content-Disposition':'attachment; filename=raport3.pdf'})
    except BadRequestKeyError:
        return noPermissions()
    
@reports.route("/commentsBorrows", methods=['GET', 'POST'])
def commentsBorrowReport():
    from app import mysql
    try:
        chosenYear = request.form['chosenYearComment']
        cursor = mysql.connection.cursor()
        cursor.execute(f'''
        SELECT wypozyczenia.IdWyp, czytelnicy.ImieCz, czytelnicy.NazwiskoCz, wypozyczenia.FaktDataZwr, wypozyczenia.Uwagi
        FROM wypozyczenia
        JOIN czytelnicy ON wypozyczenia.IdCz = czytelnicy.IdCz
        WHERE wypozyczenia.Uwagi IS NOT NULL AND wypozyczenia.Uwagi <> '' AND EXTRACT(YEAR FROM wypozyczenia.FaktDataZwr) = %s
        ORDER BY EXTRACT(MONTH FROM wypozyczenia.FaktDataZwr);
        ''', (chosenYear, ))
        result = cursor.fetchall()
        pdf, col_width, th = setFpdfObject(f'Wypożyczenia ze zgłoszonymi uwagami w roku {chosenYear} z danymi czytelników ', 2)
        
        headers = ["IdWyp", "Imię", "Nazwisko",  "DataZwr", "Uwagi"]
        colWidths = [14, 35, 50, 25, 65]
        for header, width in zip(headers, colWidths):
            pdf.cell(width, th, header, border=1)
        pdf.ln(th)
        
        for row in result:
            for header, width, value in zip(headers, colWidths, row):
                if header == "Uwagi":
                    pdf.multi_cell(width, th, str(value), border=1)
                else:
                    pdf.cell(width, th, str(value), border=1)
            pdf.ln(th)
            
        cursor.close()
        return Response(pdf.output(dest='S').encode('latin-1'), mimetype='application/pdf', headers={'Content-Disposition':'attachment; filename=raport4.pdf'})
    except BadRequestKeyError:
        return noPermissions()