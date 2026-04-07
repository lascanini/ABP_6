-- ============================================================
-- LECCIÓN 1: Las bases de datos relacionales
-- Objetivo: Crear la estructura base del sistema
-- ============================================================

-- Activar soporte de claves foráneas en SQLite
PRAGMA foreign_keys = ON;

-- ============================================================
-- LECCIÓN 2: Consultas a una sola tabla
-- Objetivo: Crear tabla Clientes, insertar datos y consultar
-- ============================================================

CREATE TABLE IF NOT EXISTS Clientes (
    id_cliente   INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre       TEXT    NOT NULL,
    apellido     TEXT    NOT NULL,
    email        TEXT    UNIQUE NOT NULL,
    telefono     TEXT,
    ciudad       TEXT    NOT NULL,
    fecha_alta   TEXT    DEFAULT (DATE('now'))
);

-- Inserción de datos de ejemplo
INSERT INTO Clientes (nombre, apellido, email, telefono, ciudad) VALUES
    ('Ana',      'González',  'ana.gonzalez@mail.com',  '11-1111-1111', 'Buenos Aires'),
    ('Carlos',   'Pérez',     'carlos.perez@mail.com',  '11-2222-2222', 'Córdoba'),
    ('Lucía',    'Martínez',  'lucia.martinez@mail.com','11-3333-3333', 'Rosario'),
    ('Martín',   'López',     'martin.lopez@mail.com',  '11-4444-4444', 'Buenos Aires'),
    ('Sofía',    'Rodríguez', 'sofia.rodriguez@mail.com','11-5555-5555','Mendoza');

-- Consultas Lección 2
-- Todos los clientes
SELECT * FROM Clientes;

-- Filtrar por ciudad
SELECT * FROM Clientes WHERE ciudad = 'Buenos Aires';

-- Filtrar por nombre
SELECT * FROM Clientes WHERE nombre LIKE 'A%';

-- ============================================================
-- LECCIÓN 3: Consultas a tablas relacionadas
-- Objetivo: Crear Productos y Ventas, usar JOIN
-- ============================================================

CREATE TABLE IF NOT EXISTS Productos (
    id_producto  INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre       TEXT    NOT NULL,
    descripcion  TEXT,
    precio       REAL    NOT NULL CHECK(precio > 0),
    categoria    TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS Ventas (
    id_venta     INTEGER PRIMARY KEY AUTOINCREMENT,
    id_cliente   INTEGER NOT NULL,
    id_producto  INTEGER NOT NULL,
    cantidad     INTEGER NOT NULL CHECK(cantidad > 0),
    fecha_venta  TEXT    DEFAULT (DATE('now')),
    total        REAL    NOT NULL,
    FOREIGN KEY (id_cliente)  REFERENCES Clientes(id_cliente),
    FOREIGN KEY (id_producto) REFERENCES Productos(id_producto)
);

-- Datos de Productos
INSERT INTO Productos (nombre, descripcion, precio, categoria) VALUES
    ('Notebook Lenovo',  'Laptop 15" 8GB RAM',         85000.00, 'Electrónica'),
    ('Mouse Logitech',   'Mouse inalámbrico',            3500.00, 'Periféricos'),
    ('Monitor Samsung',  'Monitor 24" Full HD',         55000.00, 'Electrónica'),
    ('Teclado Redragon', 'Teclado mecánico RGB',        12000.00, 'Periféricos'),
    ('Auriculares Sony', 'Auriculares bluetooth',        9500.00, 'Audio'),
    ('Webcam Logitech',  'Webcam HD 1080p',              7200.00, 'Periféricos');

-- Datos de Ventas
INSERT INTO Ventas (id_cliente, id_producto, cantidad, fecha_venta, total) VALUES
    (1, 1, 1, '2025-01-10', 85000.00),
    (1, 2, 2, '2025-01-15', 7000.00),
    (2, 3, 1, '2025-01-20', 55000.00),
    (3, 4, 1, '2025-02-01', 12000.00),
    (3, 5, 2, '2025-02-05', 19000.00),
    (4, 2, 1, '2025-02-10', 3500.00),
    (4, 6, 1, '2025-02-12', 7200.00),
    (5, 1, 1, '2025-03-01', 85000.00),
    (2, 5, 1, '2025-03-05', 9500.00),
    (1, 4, 1, '2025-03-10', 12000.00);

-- Consultas Lección 3 - JOIN
-- Qué cliente compró qué producto y cuándo
SELECT
    c.nombre || ' ' || c.apellido AS cliente,
    p.nombre                      AS producto,
    v.cantidad,
    v.total,
    v.fecha_venta
FROM Ventas v
JOIN Clientes  c ON v.id_cliente  = c.id_cliente
JOIN Productos p ON v.id_producto = p.id_producto
ORDER BY v.fecha_venta;

-- ============================================================
-- LECCIÓN 4: Consultas agrupadas
-- Objetivo: Funciones de agregación
-- ============================================================

-- Total de ventas por cliente
SELECT
    c.nombre || ' ' || c.apellido AS cliente,
    COUNT(v.id_venta)             AS cantidad_compras,
    SUM(v.total)                  AS total_gastado,
    AVG(v.total)                  AS ticket_promedio
FROM Ventas v
JOIN Clientes c ON v.id_cliente = c.id_cliente
GROUP BY v.id_cliente
ORDER BY total_gastado DESC;

-- Total de ventas por producto
SELECT
    p.nombre          AS producto,
    COUNT(v.id_venta) AS veces_vendido,
    SUM(v.cantidad)   AS unidades_vendidas,
    SUM(v.total)      AS ingresos_generados
FROM Ventas v
JOIN Productos p ON v.id_producto = p.id_producto
GROUP BY v.id_producto
ORDER BY ingresos_generados DESC;

-- Resumen general del período
SELECT
    COUNT(id_venta)  AS total_transacciones,
    SUM(total)       AS facturacion_total,
    AVG(total)       AS ticket_promedio_global,
    MAX(total)       AS venta_mas_alta,
    MIN(total)       AS venta_mas_baja
FROM Ventas;

-- ============================================================
-- LECCIÓN 5: Consultas anidadas (subconsultas)
-- Objetivo: Resolver consultas más complejas
-- ============================================================

-- Clientes que hicieron más de una compra
SELECT
    c.nombre || ' ' || c.apellido AS cliente,
    c.email,
    sub.total_compras
FROM Clientes c
JOIN (
    SELECT id_cliente, COUNT(*) AS total_compras
    FROM Ventas
    GROUP BY id_cliente
    HAVING COUNT(*) > 1
) sub ON c.id_cliente = sub.id_cliente
ORDER BY sub.total_compras DESC;

-- Producto más vendido (por unidades)
SELECT
    p.nombre,
    p.categoria,
    p.precio,
    total_unidades
FROM Productos p
JOIN (
    SELECT id_producto, SUM(cantidad) AS total_unidades
    FROM Ventas
    GROUP BY id_producto
) sub ON p.id_producto = sub.id_producto
WHERE sub.total_unidades = (
    SELECT MAX(suma)
    FROM (
        SELECT SUM(cantidad) AS suma
        FROM Ventas
        GROUP BY id_producto
    )
);

-- Cliente que más gastó en total
SELECT
    c.nombre || ' ' || c.apellido AS cliente,
    c.ciudad,
    SUM(v.total) AS total_gastado
FROM Ventas v
JOIN Clientes c ON v.id_cliente = c.id_cliente
GROUP BY v.id_cliente
HAVING SUM(v.total) = (
    SELECT MAX(gasto_total)
    FROM (
        SELECT SUM(total) AS gasto_total
        FROM Ventas
        GROUP BY id_cliente
    )
);

-- ============================================================
-- LECCIÓN 6: Creación y manipulación de tablas (DDL / DML)
-- Objetivo: ALTER TABLE, UPDATE, DELETE
-- ============================================================

-- Agregar columna stock a Productos
ALTER TABLE Productos ADD COLUMN stock INTEGER DEFAULT 0;

-- Cargar stock inicial
UPDATE Productos SET stock = 10 WHERE id_producto = 1; -- Notebook
UPDATE Productos SET stock = 50 WHERE id_producto = 2; -- Mouse
UPDATE Productos SET stock = 15 WHERE id_producto = 3; -- Monitor
UPDATE Productos SET stock = 30 WHERE id_producto = 4; -- Teclado
UPDATE Productos SET stock = 25 WHERE id_producto = 5; -- Auriculares
UPDATE Productos SET stock = 20 WHERE id_producto = 6; -- Webcam

-- Actualizar stock luego de registrar una venta
-- (Ejemplo: se vendieron 2 unidades del Mouse - id_venta = 2)
UPDATE Productos
SET stock = stock - (
    SELECT cantidad FROM Ventas WHERE id_venta = 2
)
WHERE id_producto = (
    SELECT id_producto FROM Ventas WHERE id_venta = 2
);

-- Verificar stock actualizado
SELECT id_producto, nombre, stock FROM Productos WHERE id_producto = 2;

-- Eliminar un producto obsoleto
-- Primero eliminamos sus ventas asociadas (integridad referencial)
DELETE FROM Ventas WHERE id_producto = 6;

-- Luego eliminamos el producto
DELETE FROM Productos WHERE id_producto = 6; -- Webcam Logitech

-- Verificar estado final de la tabla Productos
SELECT * FROM Productos;

-- Verificar que no quedan ventas huérfanas
SELECT COUNT(*) AS ventas_restantes FROM Ventas;
