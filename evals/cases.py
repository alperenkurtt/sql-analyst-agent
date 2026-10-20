CASES = [
  {
    "question": "How many customers are there?",
    "gold_sql": "SELECT COUNT(*) FROM Customers;"
  },
  {
    "question": "List the company names of all customers in Germany.",
    "gold_sql": "SELECT CompanyName FROM Customers WHERE Country = 'Germany';"
  },
  {
    "question": "What are the 5 most expensive products and their prices?",
    "gold_sql": "SELECT ProductName, UnitPrice FROM Products ORDER BY UnitPrice DESC LIMIT 5;"
  },
  {
    "question": "Which products are discontinued?",
    "gold_sql": "SELECT ProductName FROM Products WHERE Discontinued = '1';"
  },
  {
    "question": "Which countries do our suppliers come from?",
    "gold_sql": "SELECT DISTINCT Country FROM Suppliers;"
  },
  {
    "question": "Which products are out of stock?",
    "gold_sql": "SELECT ProductName FROM Products WHERE UnitsInStock = 0;"
  },
  {
    "question": "What is the average unit price of all products?",
    "gold_sql": "SELECT AVG(UnitPrice) FROM Products;"
  },
  {
    "question": "List employees whose title is 'Sales Representative'.",
    "gold_sql": "SELECT FirstName, LastName FROM Employees WHERE Title = 'Sales Representative';"
  },
  {
    "question": "How many products cost more than 50?",
    "gold_sql": "SELECT COUNT(*) FROM Products WHERE UnitPrice > 50;"
  },
  {
    "question": "Which customers have 'Restaurant' in their company name?",
    "gold_sql": "SELECT CompanyName FROM Customers WHERE CompanyName LIKE '%Restaurant%';"
  },
  {
    "question": "How many order line items are there in total?",
    "gold_sql": "SELECT COUNT(*) FROM \"Order Details\";"
  },
  {
    "question": "Which products need reordering (units in stock at or below the reorder level) and are not discontinued?",
    "gold_sql": "SELECT ProductName, UnitsInStock, ReorderLevel FROM Products WHERE UnitsInStock <= ReorderLevel AND Discontinued = '0';"
  },
  {
    "question": "List each product with its category name.",
    "gold_sql": "SELECT p.ProductName, c.CategoryName FROM Products p JOIN Categories c ON p.CategoryID = c.CategoryID;"
  },
  {
    "question": "How many products are in each category?",
    "gold_sql": "SELECT c.CategoryName, COUNT(*) AS n FROM Products p JOIN Categories c ON p.CategoryID = c.CategoryID GROUP BY c.CategoryName;"
  },
  {
    "question": "How many customers are there per country? Sort from most to least.",
    "gold_sql": "SELECT Country, COUNT(*) AS n FROM Customers GROUP BY Country ORDER BY n DESC;"
  },
  {
    "question": "Which countries have more than 5 customers?",
    "gold_sql": "SELECT Country FROM Customers GROUP BY Country HAVING COUNT(*) > 5;"
  },
  {
    "question": "How many orders has each employee handled? Show full name.",
    "gold_sql": "SELECT e.FirstName || ' ' || e.LastName AS employee, COUNT(o.OrderID) AS n FROM Employees e LEFT JOIN Orders o ON o.EmployeeID = e.EmployeeID GROUP BY e.EmployeeID ORDER BY n DESC;"
  },
  {
    "question": "How many orders did each shipper deliver?",
    "gold_sql": "SELECT s.CompanyName, COUNT(*) AS n FROM Orders o JOIN Shippers s ON o.ShipVia = s.ShipperID GROUP BY s.ShipperID;"
  },
  {
    "question": "List the names of products supplied by companies in Japan.",
    "gold_sql": "SELECT p.ProductName FROM Products p JOIN Suppliers s ON p.SupplierID = s.SupplierID WHERE s.Country = 'Japan';"
  },
  {
    "question": "What is the total revenue of order 10248?",
    "gold_sql": "SELECT SUM(UnitPrice * Quantity * (1 - Discount)) FROM \"Order Details\" WHERE OrderID = 10248;"
  },
  {
    "question": "How many orders were placed in 2016?",
    "gold_sql": "SELECT COUNT(*) FROM Orders WHERE strftime('%Y', OrderDate) = '2016';"
  },
  {
    "question": "How many orders were shipped after their required date?",
    "gold_sql": "SELECT COUNT(*) FROM Orders WHERE date(ShippedDate) > date(RequiredDate);"
  },
  {
    "question": "How many orders have not been shipped yet?",
    "gold_sql": "SELECT COUNT(*) FROM Orders WHERE ShippedDate IS NULL;"
  },
  {
    "question": "Who does each employee report to?",
    "gold_sql": "SELECT e.FirstName || ' ' || e.LastName AS employee, m.FirstName || ' ' || m.LastName AS manager FROM Employees e LEFT JOIN Employees m ON e.ReportsTo = m.EmployeeID;"
  },
  {
    "question": "Which employees have nobody reporting to them?",
    "gold_sql": "SELECT FirstName, LastName FROM Employees e WHERE NOT EXISTS (SELECT 1 FROM Employees r WHERE r.ReportsTo = e.EmployeeID);"
  },
  {
    "question": "What is the average freight cost per ship country? Top 10 highest.",
    "gold_sql": "SELECT ShipCountry, AVG(Freight) AS avg_freight FROM Orders GROUP BY ShipCountry ORDER BY avg_freight DESC LIMIT 10;"
  },
  {
    "question": "Which employees have sold products from the 'Seafood' category? (distinct names)",
    "gold_sql": "SELECT DISTINCT e.FirstName, e.LastName FROM Employees e JOIN Orders o ON o.EmployeeID = e.EmployeeID JOIN \"Order Details\" od ON od.OrderID = o.OrderID JOIN Products p ON p.ProductID = od.ProductID JOIN Categories c ON c.CategoryID = p.CategoryID WHERE c.CategoryName = 'Seafood';"
  },
  {
    "question": "Which products are priced above the average product price?",
    "gold_sql": "SELECT ProductName, UnitPrice FROM Products WHERE UnitPrice > (SELECT AVG(UnitPrice) FROM Products);"
  },
  {
    "question": "Who are the top 5 customers by total revenue?",
    "gold_sql": "SELECT c.CompanyName, SUM(od.UnitPrice * od.Quantity * (1 - od.Discount)) AS revenue FROM Customers c JOIN Orders o ON o.CustomerID = c.CustomerID JOIN \"Order Details\" od ON od.OrderID = o.OrderID GROUP BY c.CustomerID ORDER BY revenue DESC LIMIT 5;"
  },
  {
    "question": "What is the total revenue per category?",
    "gold_sql": "SELECT c.CategoryName, SUM(od.UnitPrice * od.Quantity * (1 - od.Discount)) AS revenue FROM \"Order Details\" od JOIN Products p ON p.ProductID = od.ProductID JOIN Categories c ON c.CategoryID = p.CategoryID GROUP BY c.CategoryName ORDER BY revenue DESC;"
  },
  {
    "question": "Show total revenue by year.",
    "gold_sql": "SELECT strftime('%Y', o.OrderDate) AS year, SUM(od.UnitPrice * od.Quantity * (1 - od.Discount)) AS revenue FROM Orders o JOIN \"Order Details\" od ON od.OrderID = o.OrderID GROUP BY year ORDER BY year;"
  },
  {
    "question": "What are the 10 best-selling products by quantity sold?",
    "gold_sql": "SELECT p.ProductName, SUM(od.Quantity) AS qty FROM \"Order Details\" od JOIN Products p ON p.ProductID = od.ProductID GROUP BY p.ProductID ORDER BY qty DESC LIMIT 10;"
  },
  {
    "question": "For each category, what is the most expensive product?",
    "gold_sql": "SELECT CategoryName, ProductName, UnitPrice FROM (SELECT c.CategoryName, p.ProductName, p.UnitPrice, RANK() OVER (PARTITION BY p.CategoryID ORDER BY p.UnitPrice DESC) AS rk FROM Products p JOIN Categories c ON c.CategoryID = p.CategoryID) WHERE rk = 1;"
  },
  {
    "question": "Which employee generated the most revenue? Show their full name as a single column and the revenue.",
    "gold_sql": "SELECT e.FirstName || ' ' || e.LastName AS employee, SUM(od.UnitPrice * od.Quantity * (1 - od.Discount)) AS revenue FROM Employees e JOIN Orders o ON o.EmployeeID = e.EmployeeID JOIN \"Order Details\" od ON od.OrderID = o.OrderID GROUP BY e.EmployeeID ORDER BY revenue DESC LIMIT 1;"
  },
  {
    "question": "Which customers have placed more than 200 orders?",
    "gold_sql": "SELECT c.CompanyName, COUNT(*) AS n FROM Customers c JOIN Orders o ON o.CustomerID = c.CustomerID GROUP BY c.CustomerID HAVING COUNT(*) > 200 ORDER BY n DESC;"
  },
  {
    "question": "What is the average number of days between order date and ship date, per shipper?",
    "gold_sql": "SELECT s.CompanyName, AVG(julianday(date(o.ShippedDate)) - julianday(date(o.OrderDate))) AS avg_days FROM Orders o JOIN Shippers s ON s.ShipperID = o.ShipVia WHERE o.ShippedDate IS NOT NULL GROUP BY s.ShipperID;"
  },
  {
    "question": "What percentage of total revenue does each category represent?",
    "gold_sql": "SELECT c.CategoryName, ROUND(100.0 * SUM(od.UnitPrice * od.Quantity * (1 - od.Discount)) / (SELECT SUM(UnitPrice * Quantity * (1 - Discount)) FROM \"Order Details\"), 2) AS pct FROM \"Order Details\" od JOIN Products p ON p.ProductID = od.ProductID JOIN Categories c ON c.CategoryID = p.CategoryID GROUP BY c.CategoryName ORDER BY pct DESC;"
  },
  {
    "question": "For each country, who is the top customer by revenue?",
    "gold_sql": "SELECT Country, CompanyName, revenue FROM (SELECT c.Country, c.CompanyName, SUM(od.UnitPrice * od.Quantity * (1 - od.Discount)) AS revenue, RANK() OVER (PARTITION BY c.Country ORDER BY SUM(od.UnitPrice * od.Quantity * (1 - od.Discount)) DESC) AS rk FROM Customers c JOIN Orders o ON o.CustomerID = c.CustomerID JOIN \"Order Details\" od ON od.OrderID = o.OrderID WHERE c.Country IS NOT NULL GROUP BY c.CustomerID) WHERE rk = 1 ORDER BY Country;"
  },
  {
    "question": "Show the monthly number of orders in 2020, with month formatted as 'YYYY-MM'.",
    "gold_sql": "SELECT strftime('%Y-%m', date(OrderDate)) AS month, COUNT(*) AS n FROM Orders WHERE strftime('%Y', date(OrderDate)) = '2020' GROUP BY month ORDER BY month;"
  },
  {
    "question": "Which suppliers provide products in more than one category?",
    "gold_sql": "SELECT s.CompanyName FROM Suppliers s JOIN Products p ON p.SupplierID = s.SupplierID GROUP BY s.SupplierID HAVING COUNT(DISTINCT p.CategoryID) > 1;"
  },
  {
    "question": "What was the year-over-year revenue growth (%) for each year?",
    "gold_sql": "WITH y AS (SELECT strftime('%Y', o.OrderDate) AS year, SUM(od.UnitPrice * od.Quantity * (1 - od.Discount)) AS rev FROM Orders o JOIN \"Order Details\" od ON od.OrderID = o.OrderID GROUP BY year) SELECT year, rev, ROUND(100.0 * (rev - LAG(rev) OVER (ORDER BY year)) / LAG(rev) OVER (ORDER BY year), 2) AS yoy_pct FROM y ORDER BY year;"
  },
  {
    "question": "How many customers are in the USA?",
    "gold_sql": "SELECT COUNT(*) FROM Customers WHERE Country = 'USA';"
  },
  {
    "question": "List the products in the beverages category.",
    "gold_sql": "SELECT p.ProductName FROM Products p JOIN Categories c ON c.CategoryID = p.CategoryID WHERE c.CategoryName = 'Beverages';"
  }
]