-- ============================================
-- BASE DE DATOS ENTRELAZA - PAITZONE
-- Creada automáticamente desde app.py
-- ============================================

SET FOREIGN_KEY_CHECKS=0;

-- Crear base de datos
CREATE DATABASE IF NOT EXISTS `Entrelaza`;
USE `Entrelaza`;

-- Tabla: usuarios

CREATE TABLE IF NOT EXISTS `usuarios` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `nombre_completo` VARCHAR(255) NOT NULL,
    `codigo_estudiante` VARCHAR(50) UNIQUE NOT NULL,
    `carrera` VARCHAR(100) NOT NULL,
    `grado` INT NOT NULL,
    `grupo` VARCHAR(10) NOT NULL,
    `turno` VARCHAR(20) NOT NULL,
    `correo` VARCHAR(255),
    `telefono` VARCHAR(20),
    `contrasena` VARCHAR(255) NOT NULL,
    `descripcion` TEXT,
    `role` ENUM('user', 'admin') DEFAULT 'user',
    `fecha_registro` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla: carreras

CREATE TABLE IF NOT EXISTS `carreras` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `nombre` VARCHAR(100) UNIQUE NOT NULL
);

-- Tabla: equipos

CREATE TABLE IF NOT EXISTS `equipos` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `nombre_proyecto` VARCHAR(255) NOT NULL,
    `descripcion` TEXT NOT NULL,
    `max_integrantes` INT NOT NULL,
    `asesor` VARCHAR(255),
    `turno` VARCHAR(20) NOT NULL,
    `privacidad` ENUM('publico', 'privado') DEFAULT 'publico',
    `creador_id` INT NOT NULL,
    `max_mensajes` INT DEFAULT 1000,
    `fecha_creacion` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla: equipo_integrantes

CREATE TABLE IF NOT EXISTS `equipo_integrantes` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `equipo_id` INT NOT NULL,
    `usuario_id` INT NOT NULL,
    `fecha_union` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY `unique_integrante` (`equipo_id`, `usuario_id`)
);

-- Tabla: equipo_carreras

CREATE TABLE IF NOT EXISTS `equipo_carreras` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `equipo_id` INT NOT NULL,
    `carrera_id` INT NOT NULL,
    `cantidad` INT DEFAULT 1
);

-- Tabla: solicitudes

CREATE TABLE IF NOT EXISTS `solicitudes` (
    `solicitud_id` INT AUTO_INCREMENT PRIMARY KEY,
    `usuario_id` INT NOT NULL,
    `equipo_id` INT NOT NULL,
    `estado` ENUM('pendiente', 'aceptada', 'rechazada') DEFAULT 'pendiente',
    `fecha` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla: notificaciones

CREATE TABLE IF NOT EXISTS `notificaciones` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `usuario_id` INT NOT NULL,
    `mensaje` VARCHAR(255) NOT NULL,
    `tipo` ENUM('solicitud', 'respuesta') NOT NULL,
    `leida` BOOLEAN DEFAULT FALSE,
    `fecha` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `solicitud_id` INT
);

-- Tabla: mensajes_equipo

CREATE TABLE IF NOT EXISTS `mensajes_equipo` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `equipo_id` INT NOT NULL,
    `usuario_id` INT NOT NULL,
    `mensaje` TEXT NOT NULL,
    `fecha` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insertar carreras
INSERT IGNORE INTO `carreras` (`nombre`) VALUES ('Administración');
INSERT IGNORE INTO `carreras` (`nombre`) VALUES ('Gestión aduanal');
INSERT IGNORE INTO `carreras` (`nombre`) VALUES ('Biotecnología');
INSERT IGNORE INTO `carreras` (`nombre`) VALUES ('Energías alternativas');
INSERT IGNORE INTO `carreras` (`nombre`) VALUES ('Telecomunicaciones');
INSERT IGNORE INTO `carreras` (`nombre`) VALUES ('Informática');
INSERT IGNORE INTO `carreras` (`nombre`) VALUES ('Procesos de manufactura competitiva');

-- Usuario administrador por defecto
INSERT IGNORE INTO `usuarios` (
    `nombre_completo`, `codigo_estudiante`, `carrera`, `grado`, `grupo`, 
    `turno`, `correo`, `contrasena`, `role`
) VALUES (
    'Administrador Principal',
    'ADMIN001',
    'Informática',
    1,
    'A',
    'Matutino',
    'admin@alumnos.udg.mx',
    'pbkdf2:sha256:1000000$t56ZEgiN4XSJlL9S$6afc8349f1f331a327a03e18563f95c522946ccb186ac70980cc7d993c1a466a',
    'admin'
);

-- Datos de prueba (usuarios normales)
INSERT IGNORE INTO `usuarios` (
    `nombre_completo`, `codigo_estudiante`, `carrera`, `grado`, `grupo`, 
    `turno`, `correo`, `contrasena`
) VALUES 
    ('Juan Pérez García', '2024001', 'Informática', 3, 'A', 'Matutino', 'juan.perez@alumnos.udg.mx', 'pbkdf2:sha256:1000000$pDxeXcTKYx6rJRxz$3f156fcb225b213466686a0d6e21e77ec60a99e471744f63844d417e7d92cb12'),
    ('María López Hernández', '2024002', 'Administración', 4, 'B', 'Vespertino', 'maria.lopez@alumnos.udg.mx', 'pbkdf2:sha256:1000000$pDxeXcTKYx6rJRxz$3f156fcb225b213466686a0d6e21e77ec60a99e471744f63844d417e7d92cb12'),
    ('Carlos Rodríguez', '2024003', 'Telecomunicaciones', 2, 'C', 'Matutino', 'carlos.rodriguez@alumnos.udg.mx', 'pbkdf2:sha256:1000000$pDxeXcTKYx6rJRxz$3f156fcb225b213466686a0d6e21e77ec60a99e471744f63844d417e7d92cb12');

SET FOREIGN_KEY_CHECKS=1;

-- Base de datos creada exitosamente --
