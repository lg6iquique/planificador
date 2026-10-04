from django.db import models
from django.utils import timezone


# ==============================================================================
# TABLAS EXISTENTES DEL SISTEMA INDUSTRIAL (mct_*)
# managed = False para preservar fidelidad con el esquema PostgreSQL original.
# ==============================================================================

class MCTCliente(models.Model):
    idcliente = models.BigIntegerField(primary_key=True, db_column='idcliente')
    rut = models.CharField(max_length=20, null=True, blank=True, db_column='rut')
    digito = models.CharField(max_length=2, null=True, blank=True, db_column='digito')
    nombrecliente = models.CharField(max_length=255, db_column='nombrecliente')
    telefono = models.CharField(max_length=50, null=True, blank=True, db_column='telefono')
    direccion = models.CharField(max_length=255, null=True, blank=True, db_column='direccion')
    email = models.CharField(max_length=100, null=True, blank=True, db_column='email')
    estado = models.BigIntegerField(default=1, db_column='estado')

    class Meta:
        managed = False
        db_table = 'mct_cliente'
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'

    def __str__(self):
        return f"{self.nombrecliente} (ID: {self.idcliente})"


class MCTProducto(models.Model):
    idproducto = models.BigIntegerField(primary_key=True, db_column='idproducto')
    nombreproducto = models.CharField(max_length=255, db_column='nombreproducto')
    idcliente = models.ForeignKey(MCTCliente, on_delete=models.DO_NOTHING, db_column='idcliente', null=True, blank=True, db_constraint=False)
    caudal = models.BigIntegerField(null=True, blank=True, db_column='caudal')
    rpm = models.BigIntegerField(null=True, blank=True, db_column='rpm')
    altura = models.BigIntegerField(null=True, blank=True, db_column='altura')
    potencia = models.BigIntegerField(null=True, blank=True, db_column='potencia')
    estado = models.BigIntegerField(default=1, db_column='estado')

    class Meta:
        managed = False
        db_table = 'mct_producto'
        verbose_name = 'Producto / Bomba'
        verbose_name_plural = 'Productos / Bombas'

    def __str__(self):
        return f"{self.nombreproducto} (ID: {self.idproducto})"


class MCTEstadoOrden(models.Model):
    idestadoorden = models.BigIntegerField(primary_key=True, db_column='idestadoorden')
    nombreestado = models.CharField(max_length=100, db_column='nombreestado')
    estado = models.BigIntegerField(default=1, db_column='estado')

    class Meta:
        managed = False
        db_table = 'mct_estadoorden'
        verbose_name = 'Estado Orden'
        verbose_name_plural = 'Estados Orden'

    def __str__(self):
        return self.nombreestado


class MCTOrdenTrabajo(models.Model):
    idordentrabajo = models.BigIntegerField(primary_key=True, db_column='idordentrabajo')
    idcliente = models.ForeignKey(MCTCliente, on_delete=models.DO_NOTHING, db_column='idcliente', null=True, blank=True, db_constraint=False)
    idproducto = models.ForeignKey(MCTProducto, on_delete=models.DO_NOTHING, db_column='idproducto', null=True, blank=True, db_constraint=False)
    idcotizacion = models.BigIntegerField(null=True, blank=True, db_column='idcotizacion')
    idtipoorden = models.BigIntegerField(null=True, blank=True, db_column='idtipoorden')
    nombreordentrabajo = models.CharField(max_length=255, null=True, blank=True, db_column='nombreordentrabajo')
    ordencompra = models.BigIntegerField(null=True, blank=True, db_column='ordencompra')
    fecharecepcion = models.DateTimeField(null=True, blank=True, db_column='fecharecepcion')
    fechaentrega = models.DateTimeField(null=True, blank=True, db_column='fechaentrega')
    fechasolicitudentrega = models.DateTimeField(null=True, blank=True, db_column='fechasolicitudentrega')
    idusuario = models.BigIntegerField(null=True, blank=True, db_column='idusuario')
    idestadoorden = models.ForeignKey(MCTEstadoOrden, on_delete=models.DO_NOTHING, db_column='idestadoorden', null=True, blank=True, db_constraint=False)
    prioridad = models.BigIntegerField(default=1, db_column='prioridad')  # Escala comercial 1 a 5
    idfamilia = models.BigIntegerField(null=True, blank=True, db_column='idfamilia')
    fechacreacion = models.DateTimeField(null=True, blank=True, db_column='fechacreacion')
    usuariocreacion = models.CharField(max_length=100, null=True, blank=True, db_column='usuariocreacion')

    class Meta:
        managed = False
        db_table = 'mct_ordentrabajo'
        verbose_name = 'Orden de Trabajo'
        verbose_name_plural = 'Órdenes de Trabajo'

    def __str__(self):
        return f"OT-{self.idordentrabajo} ({self.nombreordentrabajo or 'Sin nombre'})"


class MCTComponente(models.Model):
    idcomponente = models.BigIntegerField(primary_key=True, db_column='idcomponente')
    nombrecomponente = models.CharField(max_length=255, db_column='nombrecomponente')
    estado = models.BigIntegerField(default=1, db_column='estado')
    cantidad = models.BigIntegerField(default=1, db_column='cantidad')
    aplicafresa = models.BooleanField(default=False, db_column='aplicafresa')
    aplicaevaluacion = models.BooleanField(default=False, db_column='aplicaevaluacion')

    class Meta:
        managed = False
        db_table = 'mct_componente'
        verbose_name = 'Componente'
        verbose_name_plural = 'Componentes'

    def __str__(self):
        return f"{self.nombrecomponente} (ID: {self.idcomponente})"


class MCTParte(models.Model):
    idparte = models.BigIntegerField(primary_key=True, db_column='idparte')
    nombreparte = models.CharField(max_length=255, db_column='nombreparte')
    idplano = models.BigIntegerField(null=True, blank=True, db_column='idplano')
    idmaterial = models.BigIntegerField(null=True, blank=True, db_column='idmaterial')
    idtipoparte = models.BigIntegerField(null=True, blank=True, db_column='idtipoparte')
    costofabricacion = models.IntegerField(null=True, blank=True, db_column='costofabricacion')
    esprincipal = models.BigIntegerField(default=0, db_column='esprincipal')
    escritico = models.BigIntegerField(default=0, db_column='escritico')
    estado = models.BigIntegerField(default=1, db_column='estado')

    class Meta:
        managed = False
        db_table = 'mct_parte'
        verbose_name = 'Parte'
        verbose_name_plural = 'Partes'

    def __str__(self):
        return f"{self.nombreparte} (ID: {self.idparte})"


class MCTOrdenTrabajoParte(models.Model):
    idordentrabajoparte = models.BigIntegerField(primary_key=True, db_column='idordentrabajoparte')
    idordentrabajo = models.ForeignKey(MCTOrdenTrabajo, on_delete=models.DO_NOTHING, db_column='idordentrabajo', db_constraint=False, related_name='partes')
    idparte = models.ForeignKey(MCTParte, on_delete=models.DO_NOTHING, db_column='idparte', null=True, blank=True, db_constraint=False)
    idcomponente = models.ForeignKey(MCTComponente, on_delete=models.DO_NOTHING, db_column='idcomponente', null=True, blank=True, db_constraint=False)
    itemparte = models.BigIntegerField(null=True, blank=True, db_column='itemparte')
    itemcorr = models.BigIntegerField(null=True, blank=True, db_column='itemcorr')

    class Meta:
        managed = False
        db_table = 'mct_ordentrabajoparte'
        verbose_name = 'Parte de Orden de Trabajo'
        verbose_name_plural = 'Partes de Órdenes de Trabajo'

    def __str__(self):
        return f"OTParte-{self.idordentrabajoparte} (OT: {self.idordentrabajo_id})"


class MCTHojaRuta(models.Model):
    idhojaruta = models.BigIntegerField(primary_key=True, db_column='idhojaruta')
    idordentrabajoparte = models.ForeignKey(MCTOrdenTrabajoParte, on_delete=models.DO_NOTHING, db_column='idordentrabajoparte', null=True, blank=True, db_constraint=False, related_name='hojas_ruta')
    codhojaruta = models.CharField(max_length=50, null=True, blank=True, db_column='codhojaruta')
    fechacreacion = models.DateTimeField(null=True, blank=True, db_column='fechacreacion')
    fechafundicion = models.DateTimeField(null=True, blank=True, db_column='fechafundicion')
    modalidad = models.BigIntegerField(default=1, db_column='modalidad')

    class Meta:
        managed = False
        db_table = 'mct_hojaruta'
        verbose_name = 'Hoja de Ruta'
        verbose_name_plural = 'Hojas de Ruta'

    def __str__(self):
        return f"HR-{self.codhojaruta or self.idhojaruta}"


class MCTSeccion(models.Model):
    idseccion = models.BigIntegerField(primary_key=True, db_column='idseccion')
    nombreseccion = models.CharField(max_length=100, db_column='nombreseccion')
    codigoseccion = models.CharField(max_length=20, null=True, blank=True, db_column='codigoseccion')
    estado = models.BigIntegerField(default=1, db_column='estado')

    class Meta:
        managed = False
        db_table = 'mct_seccion'
        verbose_name = 'Sección'
        verbose_name_plural = 'Secciones'

    def __str__(self):
        return self.nombreseccion


class MCTActividad(models.Model):
    idactividad = models.BigIntegerField(primary_key=True, db_column='idactividad')
    nombreactividad = models.CharField(max_length=150, db_column='nombreactividad')
    estado = models.BigIntegerField(default=1, db_column='estado')

    class Meta:
        managed = False
        db_table = 'mct_actividad'
        verbose_name = 'Actividad'
        verbose_name_plural = 'Actividades'

    def __str__(self):
        return self.nombreactividad


class MCTMaquina(models.Model):
    idmaquina = models.BigIntegerField(primary_key=True, db_column='idmaquina')
    idsubseccion = models.BigIntegerField(null=True, blank=True, db_column='idsubseccion')
    nombremaquina = models.CharField(max_length=100, db_column='nombremaquina')
    codigomaquina = models.CharField(max_length=20, null=True, blank=True, db_column='codigomaquina')
    estado = models.IntegerField(default=1, db_column='estado')

    class Meta:
        managed = False
        db_table = 'mct_maquina'
        verbose_name = 'Máquina'
        verbose_name_plural = 'Máquinas'

    def __str__(self):
        return f"{self.nombremaquina} ({self.codigomaquina or self.idmaquina})"


class MCTOperador(models.Model):
    idoperador = models.BigIntegerField(primary_key=True, db_column='idoperador')
    nombreoperador = models.CharField(max_length=150, db_column='nombreoperador')
    rut = models.CharField(max_length=20, null=True, blank=True, db_column='rut')
    idmaquina = models.ForeignKey(MCTMaquina, on_delete=models.DO_NOTHING, db_column='idmaquina', null=True, blank=True, db_constraint=False)
    idseccionprincipal = models.ForeignKey(MCTSeccion, on_delete=models.DO_NOTHING, db_column='idseccionprincipal', null=True, blank=True, db_constraint=False)
    idperfil = models.BigIntegerField(null=True, blank=True, db_column='idperfil')
    estado = models.BigIntegerField(default=1, db_column='estado')

    class Meta:
        managed = False
        db_table = 'mct_operador'
        verbose_name = 'Operador'
        verbose_name_plural = 'Operadores'

    def __str__(self):
        return self.nombreoperador


class MCTMovimientoOrdenTrabajo(models.Model):
    idmovimientoordentrabajo = models.BigIntegerField(primary_key=True, db_column='idmovimientoordentrabajo')
    idordentrabajo = models.ForeignKey(MCTOrdenTrabajo, on_delete=models.DO_NOTHING, db_column='idordentrabajo', null=True, blank=True, db_constraint=False, related_name='movimientos')
    idhojaruta = models.ForeignKey(MCTHojaRuta, on_delete=models.DO_NOTHING, db_column='idhojaruta', null=True, blank=True, db_constraint=False, related_name='movimientos')
    codhojaruta = models.CharField(max_length=50, null=True, blank=True, db_column='codhojaruta')
    idparte = models.ForeignKey(MCTParte, on_delete=models.DO_NOTHING, db_column='idparte', null=True, blank=True, db_constraint=False)
    idmaquina = models.ForeignKey(MCTMaquina, on_delete=models.DO_NOTHING, db_column='idmaquina', null=True, blank=True, db_constraint=False, related_name='movimientos')
    idseccion = models.ForeignKey(MCTSeccion, on_delete=models.DO_NOTHING, db_column='idseccion', null=True, blank=True, db_constraint=False)
    idactividad = models.ForeignKey(MCTActividad, on_delete=models.DO_NOTHING, db_column='idactividad', null=True, blank=True, db_constraint=False)
    idaccion = models.BigIntegerField(null=True, blank=True, db_column='idaccion')
    fechainicio = models.DateTimeField(null=True, blank=True, db_column='fechainicio')
    fechatermino = models.DateTimeField(null=True, blank=True, db_column='fechatermino')
    codigoaccion = models.CharField(max_length=50, null=True, blank=True, db_column='codigoaccion')
    estadoactividad = models.BigIntegerField(default=1, db_column='estadoactividad')  # 1: En proceso / abierto, 2: Terminado / cerrado, 3: Bloqueado
    numeroinspeccion = models.CharField(max_length=50, null=True, blank=True, db_column='numeroinspeccion')
    idoperador = models.ForeignKey(MCTOperador, on_delete=models.DO_NOTHING, db_column='idoperador', null=True, blank=True, db_constraint=False, related_name='movimientos')
    tiempotrabajado = models.BigIntegerField(null=True, blank=True, db_column='tiempotrabajado')
    idmotivocierre = models.BigIntegerField(null=True, blank=True, db_column='idmotivocierre')
    idcausacierre = models.BigIntegerField(null=True, blank=True, db_column='idcausacierre')
    observacion = models.CharField(max_length=500, null=True, blank=True, db_column='observacion')
    reprocesosol = models.CharField(max_length=100, null=True, blank=True, db_column='reprocesosol')
    reprocesocc = models.CharField(max_length=100, null=True, blank=True, db_column='reprocesocc')
    checkncbomba = models.BooleanField(default=False, db_column='checkncbomba')

    class Meta:
        managed = False
        db_table = 'mct_movimientoordentrabajo'
        verbose_name = 'Movimiento de Orden de Trabajo'
        verbose_name_plural = 'Movimientos de Órdenes de Trabajo'

    def __str__(self):
        return f"Mov-{self.idmovimientoordentrabajo} (OT: {self.idordentrabajo_id})"


class MCTSLA(models.Model):
    idsla = models.BigIntegerField(primary_key=True, db_column='idsla')
    nombresla = models.CharField(max_length=100, db_column='nombresla')
    idestadoinicial = models.BigIntegerField(null=True, blank=True, db_column='idestadoinicial')
    idestadofinal = models.BigIntegerField(null=True, blank=True, db_column='idestadofinal')
    escritico = models.BigIntegerField(default=0, db_column='escritico')
    diastramo = models.BigIntegerField(null=True, blank=True, db_column='diastramo')
    estado = models.BigIntegerField(default=1, db_column='estado')

    class Meta:
        managed = False
        db_table = 'mct_sla'
        verbose_name = 'SLA'
        verbose_name_plural = 'SLAs'

    def __str__(self):
        return f"{self.nombresla} (ID: {self.idsla})"


class MCTProgAvisos(models.Model):
    idprogaviso = models.BigAutoField(primary_key=True, db_column='idprogaviso')
    idordentrabajo = models.ForeignKey(MCTOrdenTrabajo, on_delete=models.DO_NOTHING, db_column='idordentrabajo', db_constraint=False, related_name='prog_avisos')
    idsla = models.ForeignKey(MCTSLA, on_delete=models.DO_NOTHING, db_column='idsla', db_constraint=False)
    fecha_inicio = models.DateTimeField(db_column='fecha_inicio')
    fecha_termino = models.DateTimeField(db_column='fecha_termino')
    fecha_inicio_aviso = models.DateTimeField(null=True, blank=True, db_column='fecha_inicio_aviso')
    dias_tramo = models.SmallIntegerField(null=True, blank=True, db_column='dias_tramo')
    estado = models.SmallIntegerField(default=1, db_column='estado')
    fecha_real_termino = models.DateTimeField(null=True, blank=True, db_column='fecha_real_termino')
    ordenproceso = models.SmallIntegerField(default=1, db_column='ordenproceso')

    class Meta:
        managed = False
        db_table = 'mct_progavisos'
        verbose_name = 'Programación de Aviso (SLA)'
        verbose_name_plural = 'Programaciones de Avisos (SLAs)'

    def __str__(self):
        return f"ProgAviso OT-{self.idordentrabajo_id} SLA-{self.idsla_id}"


class MCTMovimientoBloqueo(models.Model):
    idmovimientobloqueo = models.BigIntegerField(primary_key=True, db_column='idmovimientobloqueo')
    idregistrotrabajo = models.BigIntegerField(null=True, blank=True, db_column='idregistrotrabajo')
    codhojaruta = models.CharField(max_length=50, null=True, blank=True, db_column='codhojaruta')
    idoperador = models.ForeignKey(MCTOperador, on_delete=models.DO_NOTHING, db_column='idoperador', null=True, blank=True, db_constraint=False)
    idseccion = models.ForeignKey(MCTSeccion, on_delete=models.DO_NOTHING, db_column='idseccion', null=True, blank=True, db_constraint=False)
    idmotivobloqueo = models.BigIntegerField(null=True, blank=True, db_column='idmotivobloqueo')
    fecharebloqueo = models.DateTimeField(null=True, blank=True, db_column='fecharebloqueo')
    fechadesbloqueo = models.DateTimeField(null=True, blank=True, db_column='fechadesbloqueo')
    idoperadordesbloquea = models.BigIntegerField(null=True, blank=True, db_column='idoperadordesbloquea')
    estadobloqueo = models.BigIntegerField(default=1, db_column='estadobloqueo')

    class Meta:
        managed = False
        db_table = 'mct_movimientobloqueo'
        verbose_name = 'Bloqueo de Movimiento'
        verbose_name_plural = 'Bloqueos de Movimientos'

    def __str__(self):
        return f"Bloqueo-{self.idmovimientobloqueo} (HR: {self.codhojaruta})"


# ==============================================================================
# TABLAS PROPIAS DE LA POC (poc_*)
# managed = True para ser administradas nativamente por Django
# ==============================================================================

class PocConfigPriorizacion(models.Model):
    nombre = models.CharField(max_length=100, default='Configuración Estándar POC')
    peso_due_date = models.FloatField(default=0.40, help_text='Peso Fecha de Entrega (0.0 a 1.0)')
    peso_holgura = models.FloatField(default=0.25, help_text='Peso Holgura Operacional (0.0 a 1.0)')
    peso_impacto = models.FloatField(default=0.20, help_text='Peso Impacto / Criticidad de Componentes (0.0 a 1.0)')
    peso_wspt = models.FloatField(default=0.10, help_text='Peso Regla WSPT (0.0 a 1.0)')
    peso_comercial = models.FloatField(default=0.05, help_text='Peso Prioridad Comercial (0.0 a 1.0)')
    umbral_amarillo_horas = models.FloatField(default=2.0, help_text='Desviación en horas para semáforo AMARILLO')
    umbral_rojo_horas = models.FloatField(default=6.0, help_text='Desviación en horas para semáforo ROJO')
    costo_hora_hombre = models.FloatField(default=25.0, help_text='Costo hora hombre (USD/CLP)')
    costo_hora_maquina = models.FloatField(default=45.0, help_text='Costo hora máquina (USD/CLP)')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'poc_config_priorizacion'
        verbose_name = 'Configuración de Priorización POC'
        verbose_name_plural = 'Configuraciones de Priorización POC'

    def __str__(self):
        return f"{self.nombre} ({'Activa' if self.is_active else 'Inactiva'})"


class PocPlanificacion(models.Model):
    ESTADOS = [
        ('BORRADOR', 'Borrador / Propuesta'),
        ('APROBADA', 'Aprobada por Planificador'),
        ('MODIFICADA', 'Modificada por Planificador'),
        ('RECHAZADA', 'Rechazada por Planificador'),
    ]
    codigo = models.CharField(max_length=50, unique=True)
    fecha_planificacion = models.DateField(default=timezone.now)
    descripcion = models.TextField(blank=True, default='')
    estado = models.CharField(max_length=20, choices=ESTADOS, default='BORRADOR')
    observaciones = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'poc_planificacion'
        verbose_name = 'Planificación POC'
        verbose_name_plural = 'Planificaciones POC'

    def __str__(self):
        return f"Plan-{self.codigo} ({self.get_estado_display()})"


class PocPlanificacionDetalle(models.Model):
    DECISIONES = [
        ('PROPUESTO', 'Propuesto por Sistema'),
        ('ACEPTADO', 'Aceptado por Humano'),
        ('MODIFICADO', 'Modificado por Humano'),
        ('RECHAZADO', 'Rechazado por Humano'),
    ]
    planificacion = models.ForeignKey(PocPlanificacion, on_delete=models.CASCADE, related_name='detalles')
    orden_trabajo = models.ForeignKey(MCTOrdenTrabajo, on_delete=models.DO_NOTHING, db_constraint=False)
    movimiento = models.ForeignKey(MCTMovimientoOrdenTrabajo, on_delete=models.DO_NOTHING, db_constraint=False, null=True, blank=True)
    maquina = models.ForeignKey(MCTMaquina, on_delete=models.DO_NOTHING, db_constraint=False)
    orden_secuencia = models.IntegerField(default=1)
    fecha_inicio_estimada = models.DateTimeField()
    fecha_fin_estimada = models.DateTimeField()
    duracion_estimada_horas = models.FloatField(default=0.0)
    score_prioridad = models.FloatField(default=0.0)
    decision_humana = models.CharField(max_length=20, choices=DECISIONES, default='PROPUESTO')
    nota_planificador = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'poc_planificacion_detalle'
        ordering = ['maquina', 'orden_secuencia']
        verbose_name = 'Detalle de Planificación POC'
        verbose_name_plural = 'Detalles de Planificación POC'

    def __str__(self):
        return f"Sec {self.orden_secuencia}: OT-{self.orden_trabajo_id} en {self.maquina}"


class PocSimulacion(models.Model):
    ESCENARIOS = [
        ('A', 'Escenario A: Minimizar Costo / Horas'),
        ('B', 'Escenario B: Maximizar Cumplimiento de Fecha'),
        ('C', 'Escenario C: Balanceado (Costo vs Servicio)'),
    ]
    codigo = models.CharField(max_length=50, unique=True)
    fecha_simulacion = models.DateTimeField(auto_now_add=True)
    orden_urgente = models.ForeignKey(MCTOrdenTrabajo, on_delete=models.DO_NOTHING, db_constraint=False)
    escenario = models.CharField(max_length=2, choices=ESCENARIOS, default='A')
    descripcion_escenario = models.CharField(max_length=255, default='')
    ots_desplazadas_count = models.IntegerField(default=0)
    horas_retraso_total = models.FloatField(default=0.0)
    costo_oportunidad_total = models.FloatField(default=0.0)
    maquinas_saturadas_count = models.IntegerField(default=0)
    resultado_json = models.JSONField(default=dict)

    class Meta:
        db_table = 'poc_simulacion'
        verbose_name = 'Simulación de Urgencia POC'
        verbose_name_plural = 'Simulaciones de Urgencia POC'

    def __str__(self):
        return f"Sim-{self.codigo} (Escenario {self.escenario}) OT-{self.orden_urgente_id}"


class PocEventoPlanificacion(models.Model):
    tipo_evento = models.CharField(max_length=50)
    descripcion = models.TextField()
    usuario = models.CharField(max_length=100, default='planificador')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'poc_evento_planificacion'
        verbose_name = 'Evento de Planificación POC'
        verbose_name_plural = 'Eventos de Planificación POC'

    def __str__(self):
        return f"[{self.tipo_evento}] {self.descripcion[:50]}"
