# 01 — Source data

Start here after downloading the project. These CSV files are the input, not
generated output. You do not need to edit them for the first run.

| File | Look for |
|---|---|
| `Sales.csv` | Orders, product and store keys, dates, quantities |
| `Products.csv` | Product names, categories, standard prices and costs |
| `Stores.csv` | Store locations; key `0` is the online store |

Try opening the first few rows of `Sales.csv`. Find `ProductKey` and `StoreKey`:
the pipeline uses them to join sales to the other two files in Step 3.

The `optional/` files are not loaded in this project. `Customers.csv` and
`Exchange_Rates.csv` are left for future experiments.

Next: [02 — Bronze](../step_02_bronze/README.md).
