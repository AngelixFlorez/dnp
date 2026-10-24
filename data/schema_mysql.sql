-- ====================================================================
-- ESQUEMA RELACIONAL DEL ÍNDICE DE DESEMPEÑO FISCAL (IDF) DEPARTAMENTAL
-- Departamento Nacional de Planeación (DNP)
-- Motor: MySQL 8.0+ / MariaDB 10.4+
-- Base de Datos: `idf`
-- ====================================================================

-- 1. Crear y seleccionar la base de datos `idf`
CREATE DATABASE IF NOT EXISTS `idf`
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE `idf`;

-- Desactivar temporalmente revisión de claves foráneas para recreación limpia
SET FOREIGN_KEY_CHECKS = 0;

-- ====================================================================
-- 2. ELIMINACIÓN DE TABLAS Y VISTAS PREVIAS (SI EXISTIERAN)
-- ====================================================================
DROP VIEW IF EXISTS `vw_visualizador_ficha`;
DROP VIEW IF EXISTS `vw_visualizador_mapa`;
DROP VIEW IF EXISTS `vw_visualizador_evolucion_nacional`;

DROP TABLE IF EXISTS `resultado_idf_anual`;
DROP TABLE IF EXISTS `evaluacion_gestion_territorial`;
DROP TABLE IF EXISTS `evaluacion_resultados_fiscales`;
DROP TABLE IF EXISTS `insumo_presupuestal_cuipo`;
DROP TABLE IF EXISTS `clasificacion_anual`;
DROP TABLE IF EXISTS `catalogo_rango_desempeno`;
DROP TABLE IF EXISTS `vigencia_fiscal`;
DROP TABLE IF EXISTS `departamento`;

-- ====================================================================
-- 3. CREACIÓN DE TABLAS MAESTRAS (CATÁLOGOS FIJOS)
-- ====================================================================

-- Tabla 1: Catálogo Oficial de Departamentos (32 Entidades Territoriales)
CREATE TABLE `departamento` (
    `codigo_divipola_2` VARCHAR(2) NOT NULL,
    `codigo_divipola_5` VARCHAR(5) NOT NULL,
    `nombre` VARCHAR(100) NOT NULL,
    `nombre_visual` VARCHAR(100) NOT NULL,
    `region` VARCHAR(50) NOT NULL,
    `activo` TINYINT(1) NOT NULL DEFAULT 1,
    `created_at` VARCHAR(30) NULL,
    PRIMARY KEY (`codigo_divipola_2`),
    UNIQUE KEY `uk_depto_divipola5` (`codigo_divipola_5`),
    UNIQUE KEY `uk_depto_nombre` (`nombre`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla 2: Catálogo de Vigencias Fiscales
CREATE TABLE `vigencia_fiscal` (
    `anio` INT NOT NULL,
    `descripcion` VARCHAR(100) NOT NULL,
    `es_vigencia_activa` TINYINT(1) NOT NULL DEFAULT 0,
    `fecha_publicacion_dnp` VARCHAR(30) NULL,
    PRIMARY KEY (`anio`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla 3: Catálogo de Rangos Institucionales de Desempeño
CREATE TABLE `catalogo_rango_desempeno` (
    `rango_id` INT NOT NULL,
    `codigo` VARCHAR(20) NOT NULL,
    `nombre_completo` VARCHAR(50) NOT NULL,
    `limite_inferior` DECIMAL(6,2) NOT NULL,
    `limite_superior` DECIMAL(6,2) NOT NULL,
    `color_hex` VARCHAR(7) NOT NULL,
    `descripcion_cualitativa` TEXT NOT NULL,
    PRIMARY KEY (`rango_id`),
    UNIQUE KEY `uk_rango_codigo` (`codigo`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ====================================================================
-- 4. CREACIÓN DE TABLAS TRANSACCIONALES (HECHOS ANUALES)
-- ====================================================================

-- Tabla 4: Clasificación Anual (Categoría Ley 617 y Tipología DNP)
CREATE TABLE `clasificacion_anual` (
    `departamento_id` VARCHAR(2) NOT NULL,
    `anio` INT NOT NULL,
    `categoria_ley_617` VARCHAR(20) NOT NULL,
    `tipologia_dnp` INT NULL,
    `observacion` TEXT NULL,
    PRIMARY KEY (`departamento_id`, `anio`),
    KEY `idx_clasif_anio` (`anio`),
    CONSTRAINT `fk_clasif_departamento` FOREIGN KEY (`departamento_id`) REFERENCES `departamento` (`codigo_divipola_2`) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT `fk_clasif_vigencia` FOREIGN KEY (`anio`) REFERENCES `vigencia_fiscal` (`anio`) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla 5: Insumos Presupuestales y Contables CUIPO (21 Cuentas)
CREATE TABLE `insumo_presupuestal_cuipo` (
    `departamento_id` VARCHAR(2) NOT NULL,
    `anio` INT NOT NULL,
    `ingresos_tributarios_a1000` DECIMAL(18,2) NULL,
    `ingresos_no_tributarios_a2000` DECIMAL(18,2) NULL,
    `transferencias_corrientes_a3010` DECIMAL(18,2) NULL,
    `transferencias_nacionales_d1000` DECIMAL(18,2) NULL,
    `ingresos_totales_a` DECIMAL(18,2) NULL,
    `ingresos_corrientes_ao` DECIMAL(18,2) NULL,
    `ahorro_corriente_c` DECIMAL(18,2) NULL,
    `gasto_inversion_e` DECIMAL(18,2) NULL,
    `gasto_fbkf` DECIMAL(18,2) NULL,
    `intereses_deuda_b2000` DECIMAL(18,2) NULL,
    `deficit_superavit_total_g` DECIMAL(18,2) NULL,
    `recursos_balance_cuipo` DECIMAL(18,2) NULL,
    `desembolsos_credito` DECIMAL(18,2) NULL,
    `activos_totales` DECIMAL(18,2) NULL,
    `pasivos_totales` DECIMAL(18,2) NULL,
    `gastos_funcionamiento_icld` DECIMAL(18,2) NULL,
    `limite_ley_617` DECIMAL(6,2) NULL,
    `presupuesto_inicial` DECIMAL(18,2) NULL,
    `recaudo_efectivo` DECIMAL(18,2) NULL,
    `compromisos_inversion` DECIMAL(18,2) NULL,
    `pagos_inversion` DECIMAL(18,2) NULL,
    PRIMARY KEY (`departamento_id`, `anio`),
    KEY `idx_cuipo_anio` (`anio`),
    CONSTRAINT `fk_cuipo_departamento` FOREIGN KEY (`departamento_id`) REFERENCES `departamento` (`codigo_divipola_2`) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT `fk_cuipo_vigencia` FOREIGN KEY (`anio`) REFERENCES `vigencia_fiscal` (`anio`) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla 6: Evaluación de Resultados Fiscales (80 % Ponderación)
CREATE TABLE `evaluacion_resultados_fiscales` (
    `departamento_id` VARCHAR(2) NOT NULL,
    `anio` INT NOT NULL,
    `dep_transf_resultado` DECIMAL(10,4) NOT NULL,
    `dep_transf_calificacion` DECIMAL(6,2) NOT NULL,
    `relevancia_fbkf_resultado` DECIMAL(10,4) NOT NULL,
    `relevancia_fbkf_calificacion` DECIMAL(6,2) NOT NULL,
    `endeudamiento_resultado` DECIMAL(10,4) NOT NULL,
    `endeudamiento_calificacion` DECIMAL(6,2) NOT NULL,
    `ahorro_corriente_resultado` DECIMAL(10,4) NOT NULL,
    `ahorro_corriente_calificacion` DECIMAL(6,2) NOT NULL,
    `balance_primario_resultado` DECIMAL(10,4) NOT NULL,
    `balance_primario_calificacion` DECIMAL(6,2) NOT NULL,
    `puntaje_subtotal_resultados` DECIMAL(6,2) NOT NULL,
    `aporte_al_idf` DECIMAL(6,2) NOT NULL,
    PRIMARY KEY (`departamento_id`, `anio`),
    KEY `idx_eval_res_anio` (`anio`),
    CONSTRAINT `fk_eval_res_departamento` FOREIGN KEY (`departamento_id`) REFERENCES `departamento` (`codigo_divipola_2`) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT `fk_eval_res_vigencia` FOREIGN KEY (`anio`) REFERENCES `vigencia_fiscal` (`anio`) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla 7: Evaluación de Gestión Territorial (20 % Ponderación)
CREATE TABLE `evaluacion_gestion_territorial` (
    `departamento_id` VARCHAR(2) NOT NULL,
    `anio` INT NOT NULL,
    `holgura_resultado` DECIMAL(10,4) NOT NULL,
    `holgura_promedio_categoria` DECIMAL(10,4) NULL,
    `holgura_calificacion` DECIMAL(6,2) NOT NULL,
    `cap_prog_recaudo_resultado` DECIMAL(10,4) NOT NULL,
    `cap_prog_recaudo_calificacion` DECIMAL(6,2) NOT NULL,
    `cap_ejec_inversion_resultado` DECIMAL(10,4) NOT NULL,
    `cap_ejec_inversion_calificacion` DECIMAL(6,2) NOT NULL,
    `bonificacion_esfuerzo_propio` DECIMAL(6,2) NOT NULL DEFAULT 0.00,
    `puntaje_gestion_sin_bonos` DECIMAL(6,2) NOT NULL,
    `puntaje_gestion_con_bonos` DECIMAL(6,2) NOT NULL,
    `aporte_al_idf` DECIMAL(6,2) NOT NULL,
    PRIMARY KEY (`departamento_id`, `anio`),
    KEY `idx_eval_ges_anio` (`anio`),
    CONSTRAINT `fk_eval_ges_departamento` FOREIGN KEY (`departamento_id`) REFERENCES `departamento` (`codigo_divipola_2`) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT `fk_eval_ges_vigencia` FOREIGN KEY (`anio`) REFERENCES `vigencia_fiscal` (`anio`) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla 8: Resultado IDF Anual y Ranking Nacional
CREATE TABLE `resultado_idf_anual` (
    `departamento_id` VARCHAR(2) NOT NULL,
    `anio` INT NOT NULL,
    `puntaje_idf_sin_bonos` DECIMAL(6,2) NOT NULL,
    `puntaje_idf_final` DECIMAL(6,2) NOT NULL,
    `rango_id` INT NOT NULL,
    `ranking_nacional` INT NOT NULL,
    `variacion_puntos_porcentuales` DECIMAL(6,2) NULL,
    PRIMARY KEY (`departamento_id`, `anio`),
    UNIQUE KEY `uk_idf_anio_ranking` (`anio`, `ranking_nacional`),
    KEY `idx_idf_anio` (`anio`),
    KEY `idx_idf_rango` (`rango_id`),
    CONSTRAINT `fk_idf_departamento` FOREIGN KEY (`departamento_id`) REFERENCES `departamento` (`codigo_divipola_2`) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT `fk_idf_vigencia` FOREIGN KEY (`anio`) REFERENCES `vigencia_fiscal` (`anio`) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT `fk_idf_rango` FOREIGN KEY (`rango_id`) REFERENCES `catalogo_rango_desempeno` (`rango_id`) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ====================================================================
-- 5. CREACIÓN DE VISTAS ANALÍTICAS (OPTIMIZACIÓN DE CONSULTAS)
-- ====================================================================

-- Vista 1: Ficha Departamental Completa (Resultados + Gestión + CUIPO)
CREATE OR REPLACE VIEW `vw_visualizador_ficha` AS
SELECT
    d.codigo_divipola_2,
    d.codigo_divipola_5,
    d.nombre               AS departamento,
    d.nombre_visual,
    d.region,
    r.anio,
    c.categoria_ley_617    AS categoria,
    c.tipologia_dnp        AS tipologia,
    -- Puntajes IDF y posición
    r.puntaje_idf_final    AS idf,
    r.puntaje_idf_sin_bonos AS idf_sin_bonos,
    r.ranking_nacional     AS ranking,
    r.variacion_puntos_porcentuales AS var_pp,
    cr.rango_id,
    cr.codigo              AS rango,
    cr.nombre_completo     AS rango_completo,
    cr.color_hex,
    -- Dimensión Resultados (80 %)
    res.puntaje_subtotal_resultados  AS resultados_score,
    res.aporte_al_idf                AS resultados_aporte,
    res.dep_transf_resultado,        res.dep_transf_calificacion,
    res.relevancia_fbkf_resultado,   res.relevancia_fbkf_calificacion,
    res.endeudamiento_resultado,     res.endeudamiento_calificacion,
    res.ahorro_corriente_resultado,  res.ahorro_corriente_calificacion,
    res.balance_primario_resultado,  res.balance_primario_calificacion,
    -- Dimensión Gestión (20 %)
    ges.puntaje_gestion_con_bonos    AS gestion_score,
    ges.aporte_al_idf                AS gestion_aporte,
    ges.holgura_resultado,           ges.holgura_promedio_categoria,
    ges.holgura_calificacion,
    ges.cap_prog_recaudo_resultado,  ges.cap_prog_recaudo_calificacion,
    ges.cap_ejec_inversion_resultado, ges.cap_ejec_inversion_calificacion,
    ges.bonificacion_esfuerzo_propio,
    -- Insumos Presupuestales CUIPO
    ins.ingresos_tributarios_a1000,
    ins.ingresos_no_tributarios_a2000,
    ins.transferencias_corrientes_a3010,
    ins.transferencias_nacionales_d1000,
    ins.ingresos_totales_a,
    ins.ingresos_corrientes_ao,
    ins.ahorro_corriente_c,
    ins.gasto_inversion_e,
    ins.gasto_fbkf,
    ins.activos_totales,
    ins.pasivos_totales,
    ins.gastos_funcionamiento_icld,
    ins.limite_ley_617,
    ins.presupuesto_inicial,
    ins.recaudo_efectivo,
    ins.compromisos_inversion,
    ins.pagos_inversion
FROM resultado_idf_anual r
JOIN departamento d ON r.departamento_id = d.codigo_divipola_2
JOIN catalogo_rango_desempeno cr ON r.rango_id = cr.rango_id
JOIN clasificacion_anual c ON r.departamento_id = c.departamento_id AND r.anio = c.anio
JOIN evaluacion_resultados_fiscales res ON r.departamento_id = res.departamento_id AND r.anio = res.anio
JOIN evaluacion_gestion_territorial ges ON r.departamento_id = ges.departamento_id AND r.anio = ges.anio
LEFT JOIN insumo_presupuestal_cuipo ins ON r.departamento_id = ins.departamento_id AND r.anio = ins.anio;

-- Vista 2: Mapa Territorial de Colombia (Distribución y Coropletas)
CREATE OR REPLACE VIEW `vw_visualizador_mapa` AS
SELECT
    d.codigo_divipola_2,
    d.codigo_divipola_5,
    d.nombre              AS departamento,
    d.nombre_visual,
    d.region,
    r.anio,
    r.puntaje_idf_final   AS idf,
    r.puntaje_idf_sin_bonos,
    r.ranking_nacional    AS ranking,
    r.variacion_puntos_porcentuales AS var_pp,
    cr.rango_id,
    cr.codigo             AS rango,
    cr.nombre_completo    AS rango_completo,
    cr.color_hex,
    c.categoria_ley_617   AS categoria,
    c.tipologia_dnp       AS tipologia
FROM resultado_idf_anual r
JOIN departamento d ON r.departamento_id = d.codigo_divipola_2
JOIN catalogo_rango_desempeno cr ON r.rango_id = cr.rango_id
JOIN clasificacion_anual c ON r.departamento_id = c.departamento_id AND r.anio = c.anio;

-- Vista 3: Evolución Histórica Nacional (Promedios, Máximos, Mínimos)
CREATE OR REPLACE VIEW `vw_visualizador_evolucion_nacional` AS
SELECT
    r.anio,
    ROUND(AVG(r.puntaje_idf_final), 2)  AS idf_promedio,
    ROUND(MAX(r.puntaje_idf_final), 2)  AS idf_maximo,
    ROUND(MIN(r.puntaje_idf_final), 2)  AS idf_minimo,
    COUNT(r.departamento_id)            AS deptos_evaluados,
    ROUND(AVG(r.variacion_puntos_porcentuales), 2) AS var_pp_promedio
FROM resultado_idf_anual r
GROUP BY r.anio
ORDER BY r.anio;

-- Reactivar revisión de claves foráneas
SET FOREIGN_KEY_CHECKS = 1;

-- Mensaje de confirmación
SELECT 'Esquema de base de datos `idf` (8 tablas + 3 vistas) creado exitosamente en MySQL.' AS `Mensaje`;
