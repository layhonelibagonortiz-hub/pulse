-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Servidor: 127.0.0.1
-- Tiempo de generación: 19-09-2026 a las 15:28:56
-- Versión del servidor: 10.4.32-MariaDB
-- Versión de PHP: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de datos: `pulse_db`
--

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `carrito`
--

CREATE TABLE `carrito` (
  `id` int(11) NOT NULL,
  `usuario_id` int(11) DEFAULT NULL,
  `producto_id` int(11) DEFAULT NULL,
  `cantidad` int(11) DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `historial_canjes`
--

CREATE TABLE `historial_canjes` (
  `id` int(11) NOT NULL,
  `usuario_id` int(11) NOT NULL,
  `producto_id` int(11) NOT NULL,
  `fecha` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `pedidos`
--

CREATE TABLE `pedidos` (
  `id` int(11) NOT NULL,
  `codigo_pedido` varchar(50) NOT NULL,
  `usuario_id` int(11) DEFAULT NULL,
  `total` decimal(10,2) DEFAULT NULL,
  `fecha` timestamp NOT NULL DEFAULT current_timestamp(),
  `estado` varchar(50) DEFAULT 'En preparación',
  `articulos_count` int(11) DEFAULT NULL,
  `nombre_producto` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `productos`
--

CREATE TABLE `productos` (
  `id` int(11) NOT NULL,
  `nombre` varchar(150) NOT NULL,
  `descripcion` text DEFAULT NULL,
  `precio` decimal(10,2) NOT NULL,
  `stock` int(11) DEFAULT 0,
  `imagen` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `productos`
--

INSERT INTO `productos` (`id`, `nombre`, `descripcion`, `precio`, `stock`, `imagen`) VALUES
(1, 'Proteína Whey 2lbs', 'Suplemento de alta calidad para rendimiento.', 120000.00, 15, 'proteina.jpg'),
(2, 'Camiseta Oversize Pulse', 'Camiseta de algodón transpirable con diseño futurista ideal para entrenar.', 55000.00, 25, 'camiseta_pulse.jpg'),
(3, 'Jogger Deportivo Negro', 'Pantalón tipo jogger cómodo, flexible y de ajuste moderno para movilidad total.', 85000.00, 20, 'jogger_negro.jpg'),
(4, 'Hoodie Oversize Matrix', 'Sudadera con capucha y estilo urbano oscuro, perfecta para antes y después de entrenar.', 110000.00, 15, 'hoodie_matrix.jpg'),
(5, 'Creatina Monohidratada 300g', 'Suplemento de alta pureza para mejorar el rendimiento y la fuerza muscular.', 95000.00, 30, 'creatina.jpg');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `productos_recompensas`
--

CREATE TABLE `productos_recompensas` (
  `id` int(11) NOT NULL,
  `nombre` varchar(100) NOT NULL,
  `descripcion` text DEFAULT NULL,
  `puntos_requeridos` int(11) NOT NULL,
  `stock` int(11) NOT NULL,
  `imagen` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `rutinas_semanales`
--

CREATE TABLE `rutinas_semanales` (
  `id` int(11) NOT NULL,
  `usuario_id` int(11) NOT NULL,
  `dia_semana` varchar(20) NOT NULL,
  `ejercicios` text NOT NULL,
  `dia` varchar(20) DEFAULT NULL,
  `rutina` text DEFAULT NULL,
  `archivo_video` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `usuarios`
--

CREATE TABLE `usuarios` (
  `id` int(11) NOT NULL,
  `nombre` varchar(100) DEFAULT NULL,
  `correo` varchar(100) DEFAULT NULL,
  `telefono` varchar(50) DEFAULT NULL,
  `usuario` varchar(100) NOT NULL,
  `password` varchar(255) NOT NULL,
  `rol` varchar(50) DEFAULT 'cliente',
  `encuesta_completada` int(11) DEFAULT 0,
  `deporte_principal` varchar(100) DEFAULT NULL,
  `puntos` int(11) DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `usuarios`
--

INSERT INTO `usuarios` (`id`, `nombre`, `correo`, `telefono`, `usuario`, `password`, `rol`, `encuesta_completada`, `deporte_principal`, `puntos`) VALUES
(5, 'Santiago', 'santx9670@gmail.com', '3115272971', 'Santx', 'scrypt:32768:8:1$gMm4kPo1qRCGgft5$b666622a5a095483701b0cb8b77660d36dbb7e79ddfe06bd695de3567d564ae9c09c7ec9075430a784d6da2493bea9340bbdb08496e42d682692fc4fe0a6e2bc', 'cliente', 0, 'Fútbol', 0),
(6, 'Santi', 'sancogo09@gmail.com', '3115272971', 'Santi123', 'scrypt:32768:8:1$T8KWDfnsYH22cs0W$d74b546db3b2b530fadcf8665ee9624679747131434eb958555c7a3a81e2764b051450b59ddd7d8a0952fbacb7844385bcc11dd54baffcbcc7b294239307eaa1', 'admin', 0, 'Fútbol', 20),
(7, 'Juan', 'juan@gmail.com', '3115272971', 'Juan', 'scrypt:32768:8:1$1ZQIii9HaMfZxGis$72c7b550a18087f5adbccf4e1111e9d0a0cafa8640ef3d09fc4dbc549682a2e0d2cf89970cee41a528b929eb06536f04f07c01370daea258670b0c7fefa312ed', 'empleado', 0, 'Fútbol', 10);

--
-- Índices para tablas volcadas
--

--
-- Indices de la tabla `carrito`
--
ALTER TABLE `carrito`
  ADD PRIMARY KEY (`id`),
  ADD KEY `usuario_id` (`usuario_id`),
  ADD KEY `producto_id` (`producto_id`);

--
-- Indices de la tabla `historial_canjes`
--
ALTER TABLE `historial_canjes`
  ADD PRIMARY KEY (`id`),
  ADD KEY `usuario_id` (`usuario_id`),
  ADD KEY `producto_id` (`producto_id`);

--
-- Indices de la tabla `pedidos`
--
ALTER TABLE `pedidos`
  ADD PRIMARY KEY (`id`),
  ADD KEY `usuario_id` (`usuario_id`);

--
-- Indices de la tabla `productos`
--
ALTER TABLE `productos`
  ADD PRIMARY KEY (`id`);

--
-- Indices de la tabla `productos_recompensas`
--
ALTER TABLE `productos_recompensas`
  ADD PRIMARY KEY (`id`);

--
-- Indices de la tabla `rutinas_semanales`
--
ALTER TABLE `rutinas_semanales`
  ADD PRIMARY KEY (`id`),
  ADD KEY `usuario_id` (`usuario_id`);

--
-- Indices de la tabla `usuarios`
--
ALTER TABLE `usuarios`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `usuario` (`usuario`);

--
-- AUTO_INCREMENT de las tablas volcadas
--

--
-- AUTO_INCREMENT de la tabla `carrito`
--
ALTER TABLE `carrito`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT de la tabla `historial_canjes`
--
ALTER TABLE `historial_canjes`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `pedidos`
--
ALTER TABLE `pedidos`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- AUTO_INCREMENT de la tabla `productos`
--
ALTER TABLE `productos`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT de la tabla `productos_recompensas`
--
ALTER TABLE `productos_recompensas`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `rutinas_semanales`
--
ALTER TABLE `rutinas_semanales`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=16;

--
-- AUTO_INCREMENT de la tabla `usuarios`
--
ALTER TABLE `usuarios`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=8;

--
-- Restricciones para tablas volcadas
--

--
-- Filtros para la tabla `carrito`
--
ALTER TABLE `carrito`
  ADD CONSTRAINT `carrito_ibfk_1` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `carrito_ibfk_2` FOREIGN KEY (`producto_id`) REFERENCES `productos` (`id`) ON DELETE CASCADE;

--
-- Filtros para la tabla `historial_canjes`
--
ALTER TABLE `historial_canjes`
  ADD CONSTRAINT `historial_canjes_ibfk_1` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`),
  ADD CONSTRAINT `historial_canjes_ibfk_2` FOREIGN KEY (`producto_id`) REFERENCES `productos_recompensas` (`id`);

--
-- Filtros para la tabla `pedidos`
--
ALTER TABLE `pedidos`
  ADD CONSTRAINT `pedidos_ibfk_1` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE;

--
-- Filtros para la tabla `rutinas_semanales`
--
ALTER TABLE `rutinas_semanales`
  ADD CONSTRAINT `rutinas_semanales_ibfk_1` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
