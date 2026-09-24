# 01 — Source data

After [Step 00 — Setup](../step_00_setup/README.md), take a look at the source
CSVs. They can stay unchanged for the first pipeline run.

| File | Look for |
|---|---|
| `Sales.csv` | Orders, product and store keys, dates, quantities |
| `Products.csv` | Product names, categories, standard prices and costs |
| `Stores.csv` | Store locations; key `0` is the online store |

Try opening the first few rows of `Sales.csv`. Find `ProductKey` and `StoreKey`:
the pipeline uses them to join sales to the other two files in Step 3.

The `optional/` files are not loaded in this project. `Customers.csv` and
`Exchange_Rates.csv` are left for future experiments.

`Data_Dictionary.csv` explains the source fields. It is a reference, not a
fourth pipeline input.
The [Data Guide](../support/DATA_MODEL.md) connects those fields to Bronze,
Silver, and Gold with a flow diagram and a dictionary for each layer.

Next: [02 — Bronze](../step_02_bronze/README.md).
