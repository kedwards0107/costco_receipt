<h1> Extract receipt data from Costco PDF receipt</h1>

<h2>
  I wanted to analyze my yearly purchases from Costco but they do not have any way to extract the data as a spreadsheet you can only download each individual 
  receipt as a pdf. The following code extracts the data and combines it into one spreadsheet.
</h2>

<h3> App.py </h3>
<p>
  This code extracts data from Costco PDF receipts by using regular expressions. The regex is not perfect as some of the information is extracted incorrectly however I 
  estimate that the accuracy is >95%. The PDFs are pulled one by one from a folder named costcoPDF, the data is extracted and combined into a single csv file 
  that is then saved as costco_data_output.csv
</p>

<h3> google drive extract.py </h3>
<p>
  This code is the same as the App.py code except that the PDFs are pulled one by one from a linked google drive account and combined into one csv file the data is then combined with
  dimensional data from a csv file named Dim_costco.csv that I made to add additional details about the items. This combined data is then added to the google 
  drive. 
</p>

