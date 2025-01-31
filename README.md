# invoice generator

I made this quickly (using R1, which is very impressive) to automate [invoice.kitchen](https://www.invoice.kitchen/). As a result, the actual invoice is ripped (in an around about way) from the authors, to whom I owe my thanks.

The workflow originates with an excel sheet (`sample-sheet.xlsx`). It's a very opinionated format, but I liked it and it was quick. Enter the hours there, update your config.yaml, then run something like `python invoice.py sheet-name timesheet.xlsx`.
