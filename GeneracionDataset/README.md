## 📊 Generación de Datos de la Red

Para evaluar el algoritmo de optimización de QoS, se genera una red sintética que simula condiciones realistas de telecomunicaciones. Esta red se modela como un grafo dirigido donde cada enlace contiene métricas clave de calidad de servicio.

### 🔧 Modelo de Red

La topología de la red se construye utilizando el modelo de Barabási-Albert, el cual genera redes de libre escala. Este tipo de redes es adecuado para representar infraestructuras reales como Internet, donde algunos nodos tienen muchas conexiones (hubs).

- `n`: número de nodos en la red  
- `m`: número de conexiones nuevas por nodo  

Posteriormente, la red se convierte en dirigida, lo cual permite modelar flujos de tráfico con sentido específico.

---

### 📡 Asignación de Métricas QoS

A cada enlace del grafo se le asignan métricas fundamentales de Calidad de Servicio (QoS), simulando condiciones realistas:

#### 1. Ancho de Banda (Bandwidth)
- Rango: 10 a 200 Mbps  
- Se genera de forma aleatoria

#### 2. Latencia
- Rango base: 1 a 100 ms  
- Se ajusta según el ancho de banda (mayor ancho de banda → menor latencia adicional)

#### 3. Jitter
- Representa la variación en el retardo  
- Depende de la latencia

#### 4. Pérdida de Paquetes
- Valores típicos menores al 1%  
- Influenciados por el ancho de banda

---

### 🧠 Interpretación del Modelo

Este diseño introduce relaciones realistas entre métricas:

- Mayor ancho de banda → menor latencia y pérdida  
- Mayor latencia → mayor jitter  
- Se simula indirectamente la congestión de red  

Esto evita generar datos completamente aleatorios sin coherencia física.