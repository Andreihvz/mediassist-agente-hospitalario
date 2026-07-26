import { useEffect, useState } from "react";
import "./App.css";

const API_URL = "http://127.0.0.1:8000";

const sections = {
  chat: {
    title: "Hola, soy MediAssist 👋",
    subtitle: "¿En qué puedo ayudarte hoy?",
  },
  schedule: {
    title: "Agendar una cita",
    subtitle: "Selecciona los datos de tu consulta médica.",
  },
  appointment: {
    title: "Consultar una cita",
    subtitle: "Busca una cita utilizando su identificador.",
  },
  doctors: {
    title: "Directorio médico",
    subtitle: "Consulta nuestros médicos y especialidades.",
  },
  prices: {
    title: "Precios y estudios",
    subtitle: "Consulta costos y preparación de estudios médicos.",
  },
  faq: {
    title: "Preguntas frecuentes",
    subtitle: "Resuelve tus dudas sobre nuestros servicios.",
  },
  info: {
    title: "Información para pacientes",
    subtitle: "Políticas, convenios e indicaciones generales.",
  },
};

const mensajeInicial = {
  id: 1,
  sender: "bot",
  text: "¡Hola! Soy MediAssist. Puedo ayudarte a consultar precios, buscar médicos, resolver preguntas frecuentes y próximamente agendar citas desde esta interfaz.",
};

function App() {
  const [activeSection, setActiveSection] = useState("chat");
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([mensajeInicial]);
  const [isLoading, setIsLoading] = useState(false);

  const currentDate = new Intl.DateTimeFormat("es-MX", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  }).format(new Date());

  const currentHour = new Date().getHours();

  const greeting =
    currentHour < 12
      ? "Buenos días"
      : currentHour < 19
        ? "Buenas tardes"
        : "Buenas noches";

  const [sessionId] = useState(() => {
    const savedSession = localStorage.getItem("mediassist_session_id");

    if (savedSession) {
      return savedSession;
    }

    const newSession = `web-${Date.now()}-${Math.random()
      .toString(36)
      .slice(2, 9)}`;

    localStorage.setItem("mediassist_session_id", newSession);

    return newSession;
  });

  const changeSection = (section) => {
    setActiveSection(section);
  };

  const formatStructuredResponse = (data) => {
    if (typeof data?.respuesta === "string" && data.respuesta.trim()) {
      return data.respuesta.trim();
    }

    if (typeof data?.texto === "string" && data.texto.trim()) {
      return data.texto.trim();
    }

    return "MediAssist respondió, pero no pude mostrar el contenido.";
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    const cleanMessage = message.trim();

    if (!cleanMessage || isLoading) {
      return;
    }

    const userMessage = {
      id: Date.now(),
      sender: "user",
      text: cleanMessage,
    };

    setMessages((currentMessages) => [
      ...currentMessages,
      userMessage,
    ]);

    setMessage("");
    setIsLoading(true);

    try {
      const response = await fetch(`${API_URL}/api/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          mensaje: cleanMessage,
          sesion_id: sessionId,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data?.detail || "No fue posible procesar la consulta."
        );
      }

      const botMessage = {
        id: Date.now() + 1,
        sender: "bot",
        text: formatStructuredResponse(data),
        metadata: data.metadata,
      };

      setMessages((currentMessages) => [
        ...currentMessages,
        botMessage,
      ]);
    } catch (error) {
      console.error("Error al consultar MediAssist:", error);

      const errorMessage = {
        id: Date.now() + 1,
        sender: "bot",
        error: true,
        text:
          error.message ||
          "No pude comunicarme con el servidor de MediAssist.",
      };

      setMessages((currentMessages) => [
        ...currentMessages,
        errorMessage,
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const resetConversation = async () => {
    try {
      await fetch(`${API_URL}/api/chat/${sessionId}`, {
        method: "DELETE",
      });
    } catch (error) {
      console.error("No se pudo reiniciar la memoria:", error);
    }

    setMessages([
      {
        ...mensajeInicial,
        id: Date.now(),
      },
    ]);
  };

  const currentSection = sections[activeSection];

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">✚</div>

          <div>
            <h1>MediAssist</h1>
            <p>Asistente hospitalario</p>
          </div>
        </div>

        <nav className="menu">
          <MenuButton
            icon="💬"
            label="Chat"
            section="chat"
            activeSection={activeSection}
            changeSection={changeSection}
          />

          <MenuButton
            icon="📅"
            label="Agendar cita"
            section="schedule"
            activeSection={activeSection}
            changeSection={changeSection}
          />

          <MenuButton
            icon="🔎"
            label="Consultar cita"
            section="appointment"
            activeSection={activeSection}
            changeSection={changeSection}
          />

          <MenuButton
            icon="👨‍⚕️"
            label="Médicos"
            section="doctors"
            activeSection={activeSection}
            changeSection={changeSection}
          />

          <MenuButton
            icon="💰"
            label="Precios"
            section="prices"
            activeSection={activeSection}
            changeSection={changeSection}
          />

          <MenuButton
            icon="❓"
            label="Preguntas frecuentes"
            section="faq"
            activeSection={activeSection}
            changeSection={changeSection}
          />

          <MenuButton
            icon="📚"
            label="Información"
            section="info"
            activeSection={activeSection}
            changeSection={changeSection}
          />
        </nav>

        <div className="sidebar-footer">
          <p>Hospital MediAssist</p>
          <span>Atención inteligente 24/7</span>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div className="topbar-copy">
            <span className="greeting">{greeting} 👋</span>
            <h2>{currentSection.title}</h2>
            <p>{currentSection.subtitle}</p>
            <small>{currentDate}</small>
          </div>

          <div className="system-status">
            <div className="status">
              <span className="status-dot"></span>
              Sistema disponible
            </div>

            <div className="status secondary-status">
              🤖 Gemini activo
            </div>
          </div>
        </header>

        {activeSection === "chat" && (
          <ChatSection
            message={message}
            setMessage={setMessage}
            messages={messages}
            isLoading={isLoading}
            handleSubmit={handleSubmit}
            changeSection={changeSection}
            resetConversation={resetConversation}
          />
        )}

        {activeSection === "schedule" && <ScheduleSection />}

        {activeSection === "appointment" && <AppointmentSection />}

        {activeSection === "doctors" && <DoctorsSection />}

        {activeSection === "prices" && <PricesSection />}

        {activeSection === "faq" && <FaqSection />}

        {activeSection === "info" && <InformationSection />}
      </main>
    </div>
  );
}

function MenuButton({
  icon,
  label,
  section,
  activeSection,
  changeSection,
}) {
  return (
    <button
      className={`menu-item ${
        activeSection === section ? "active" : ""
      }`}
      onClick={() => changeSection(section)}
    >
      <span>{icon}</span>
      {label}
    </button>
  );
}

function ChatSection({
  message,
  setMessage,
  messages,
  isLoading,
  handleSubmit,
  changeSection,
  resetConversation,
}) {
  return (
    <>
      <section className="dashboard-stats">
        <article className="stat-card">
          <div className="stat-icon">💬</div>

          <div>
            <span>Conversación</span>
            <strong>{messages.length} mensajes</strong>
          </div>
        </article>

        <article className="stat-card">
          <div className="stat-icon">🩺</div>

          <div>
            <span>Servicios</span>
            <strong>6 módulos activos</strong>
          </div>
        </article>

        <article className="stat-card">
          <div className="stat-icon">🧠</div>

          <div>
            <span>Inteligencia artificial</span>
            <strong>Gemini conectado</strong>
          </div>
        </article>

        <article className="stat-card">
          <div className="stat-icon">⚡</div>

          <div>
            <span>Disponibilidad</span>
            <strong>Atención 24/7</strong>
          </div>
        </article>
      </section>

      <section className="welcome-card">
        <div className="welcome-text">
          <span className="badge">
            Asistente con inteligencia artificial
          </span>

          <h3>Bienvenido a MediAssist AI</h3>

          <p>
            Gestiona citas, consulta especialistas, revisa estudios y recibe
            orientación hospitalaria desde una sola plataforma inteligente.
          </p>
        </div>

        <div className="medical-icon">🏥</div>
      </section>

      <section className="quick-actions">
        <button
          className="action-card"
          onClick={() => changeSection("schedule")}
        >
          <span>📅</span>

          <div>
            <h4>Agendar una cita</h4>
            <p>Selecciona médico, fecha y horario.</p>
          </div>
        </button>

        <button
          className="action-card"
          onClick={() => {
            setMessage("¿Qué estudios médicos tienen y cuánto cuestan?");
          }}
        >
          <span>💳</span>

          <div>
            <h4>Consultar precios</h4>
            <p>Pregunta por costos de estudios y servicios.</p>
          </div>
        </button>

        <button
          className="action-card"
          onClick={() => {
            setMessage("¿Qué médicos y especialidades tienen disponibles?");
          }}
        >
          <span>👨‍⚕️</span>

          <div>
            <h4>Buscar médicos</h4>
            <p>Consulta especialistas directamente con la IA.</p>
          </div>
        </button>
      </section>

      <section className="chat-panel">
        <div className="chat-header">
          <div>
            <h3>Asistente virtual</h3>
            <p>Conectado con Gemini, n8n y tu base hospitalaria</p>
          </div>

          <div className="chat-header-actions">
            <span>En línea</span>

            <button
              type="button"
              className="reset-chat-button"
              onClick={resetConversation}
              disabled={isLoading}
            >
              Nueva conversación
            </button>
          </div>
        </div>

        <div className="messages">
          {messages.map((chatMessage) => (
            <div
              className={`message ${chatMessage.sender}`}
              key={chatMessage.id}
            >
              {chatMessage.sender === "bot" && (
                <div className="avatar">✚</div>
              )}

              <div
                className={`bubble ${
                  chatMessage.error ? "error-bubble" : ""
                }`}
              >
                {chatMessage.text}
              </div>

              {chatMessage.sender === "user" && (
                <div className="user-avatar">👤</div>
              )}
            </div>
          ))}

          {isLoading && (
            <div className="message bot">
              <div className="avatar">✚</div>

              <div className="bubble typing-bubble">
                <span></span>
                <span></span>
                <span></span>
                <small>MediAssist está consultando...</small>
              </div>
            </div>
          )}
        </div>

        <form className="chat-input" onSubmit={handleSubmit}>
          <input
            type="text"
            placeholder="Ejemplo: ¿Cuánto cuesta una resonancia magnética?"
            value={message}
            onChange={(event) => setMessage(event.target.value)}
            disabled={isLoading}
          />

          <button
            type="submit"
            disabled={isLoading || !message.trim()}
          >
            {isLoading ? "Consultando..." : "Enviar ➤"}
          </button>
        </form>
      </section>
    </>
  );
}

function ScheduleSection() {
  const [doctors, setDoctors] = useState([]);
  const [specialties, setSpecialties] = useState([]);
  const [selectedSpecialty, setSelectedSpecialty] = useState("");
  const [selectedDoctor, setSelectedDoctor] = useState("");

  const [patientName, setPatientName] = useState("");
  const [phone, setPhone] = useState("");
  const [date, setDate] = useState("");
  const [time, setTime] = useState("");

  const [isLoadingDoctors, setIsLoadingDoctors] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    const loadDoctors = async () => {
      setIsLoadingDoctors(true);
      setError("");

      try {
        const response = await fetch(`${API_URL}/api/medicos`);
        const data = await response.json();

        if (!response.ok) {
          throw new Error(
            data?.detail || "No fue posible cargar los médicos."
          );
        }

        const doctorList = Array.isArray(data)
          ? data
          : data.medicos || data.doctors || [];

        setDoctors(doctorList);

        const specialtyList = [
          ...new Set(
            doctorList
              .map(
                (doctor) =>
                  doctor.especialidad ||
                  doctor.Especialidad ||
                  doctor.specialty
              )
              .filter(Boolean)
          ),
        ].sort();

        setSpecialties(specialtyList);
      } catch (loadError) {
        console.error("Error al cargar médicos:", loadError);
        setError(
          loadError.message ||
            "No se pudieron cargar médicos y especialidades."
        );
      } finally {
        setIsLoadingDoctors(false);
      }
    };

    loadDoctors();
  }, []);

  const filteredDoctors = selectedSpecialty
    ? doctors.filter((doctor) => {
        const specialty =
          doctor.especialidad ||
          doctor.Especialidad ||
          doctor.specialty ||
          "";

        return specialty === selectedSpecialty;
      })
    : [];

  const getDoctorName = (doctor) =>
    doctor.nombre ||
    doctor.Nombre ||
    doctor.medico ||
    doctor.Medico ||
    doctor.nombre_completo ||
    doctor.Nombre_Completo ||
    "Médico sin nombre";

  const clearForm = () => {
    setPatientName("");
    setPhone("");
    setSelectedSpecialty("");
    setSelectedDoctor("");
    setDate("");
    setTime("");
    setMessage("");
    setError("");
  };

  const handleSchedule = async () => {
    setMessage("");
    setError("");

    if (
      !patientName.trim() ||
      !phone.trim() ||
      !selectedSpecialty ||
      !selectedDoctor ||
      !date ||
      !time
    ) {
      setError("Completa todos los campos antes de confirmar.");
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await fetch(`${API_URL}/api/citas`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          nombre: patientName.trim(),
          telefono: phone.trim(),
          especialidad: selectedSpecialty,
          medico: selectedDoctor,
          fecha: date,
          hora: time,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        const mensajeError = Array.isArray(data?.detail)
          ? data.detail.map((err) => err.msg).join(", ")
          : data?.detail || "No fue posible registrar la cita.";

        throw new Error(mensajeError);
      }

      const folio =
        data.folio ||
        data.cita?.folio ||
        data.id ||
        "Folio no disponible";

      setMessage(`Cita registrada correctamente. Folio: ${folio}`);
    } catch (scheduleError) {
      console.error("Error al agendar cita:", scheduleError);

      setError(
        scheduleError.message ||
          "Ocurrió un problema al registrar la cita."
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <section className="content-card">
      <div className="section-heading">
        <div className="section-icon">📅</div>

        <div>
          <h3>Nueva cita médica</h3>
          <p>
            Selecciona una especialidad y un médico disponible.
          </p>
        </div>
      </div>

      {error && <div className="form-alert error-alert">{error}</div>}

      {message && (
        <div className="form-alert success-alert">✅ {message}</div>
      )}

      <div className="form-grid">
        <label className="form-field">
          <span>Nombre del paciente</span>

          <input
            type="text"
            placeholder="Escribe tu nombre completo"
            value={patientName}
            onChange={(event) => setPatientName(event.target.value)}
          />
        </label>

        <label className="form-field">
          <span>Especialidad</span>

          <select
            value={selectedSpecialty}
            onChange={(event) => {
              setSelectedSpecialty(event.target.value);
              setSelectedDoctor("");
            }}
            disabled={isLoadingDoctors}
          >
            <option value="">
              {isLoadingDoctors
                ? "Cargando especialidades..."
                : "Selecciona una especialidad"}
            </option>

            {specialties.map((specialty) => (
              <option value={specialty} key={specialty}>
                {specialty}
              </option>
            ))}
          </select>
        </label>

        <label className="form-field">
          <span>Médico</span>

          <select
            value={selectedDoctor}
            onChange={(event) => setSelectedDoctor(event.target.value)}
            disabled={!selectedSpecialty || isLoadingDoctors}
          >
            <option value="">
              {!selectedSpecialty
                ? "Primero selecciona una especialidad"
                : "Selecciona un médico"}
            </option>

            {filteredDoctors.map((doctor, index) => {
              const doctorName = getDoctorName(doctor);

              return (
                <option
                  value={doctorName}
                  key={
                    doctor.id ||
                    doctor.ID_Medico ||
                    doctor.id_medico ||
                    `${doctorName}-${index}`
                  }
                >
                  {doctorName}
                </option>
              );
            })}
          </select>
        </label>

        <label className="form-field">
          <span>Fecha</span>

          <input
            type="date"
            value={date}
            min={new Date().toISOString().split("T")[0]}
            onChange={(event) => setDate(event.target.value)}
          />
        </label>

        <label className="form-field">
          <span>Hora</span>

          <input
            type="time"
            value={time}
            onChange={(event) => setTime(event.target.value)}
          />
        </label>

        <label className="form-field">
          <span>Teléfono</span>

          <input
            type="tel"
            placeholder="Ejemplo: 55 1234 5678"
            value={phone}
            onChange={(event) => setPhone(event.target.value)}
          />
        </label>
      </div>

      <div className="form-actions">
        <button
          type="button"
          className="secondary-button"
          onClick={clearForm}
          disabled={isSubmitting}
        >
          Limpiar
        </button>

        <button
          type="button"
          className="primary-button"
          onClick={handleSchedule}
          disabled={isSubmitting || isLoadingDoctors}
        >
          {isSubmitting ? "Registrando..." : "Confirmar cita"}
        </button>
      </div>
    </section>
  );
}

function AppointmentSection() {
  const [folio, setFolio] = useState("");
  const [cita, setCita] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const buscarCita = async () => {
    if (!folio.trim()) {
      setError("Ingresa un folio.");
      setCita(null);
      return;
    }

    setLoading(true);
    setError("");
    setCita(null);

    try {
      const response = await fetch(
        `${API_URL}/api/citas/${folio}`
      );

      const data = await response.json();

      if (!data.ok) {
        setError(data.mensaje);
      } else {
        setCita(data.cita);
      }
    } catch (err) {
      console.error(err);
      setError("No fue posible conectar con el servidor.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="content-card narrow-card">
      <div className="section-heading">
        <div className="section-icon">🔎</div>

        <div>
          <h3>Buscar una cita</h3>
          <p>Introduce el folio que recibiste al agendar.</p>
        </div>
      </div>

      <label className="form-field">
        <span>Folio de la cita</span>

        <input
          type="text"
          placeholder="Ejemplo: CIT-20260722195330"
          value={folio}
          onChange={(e) => setFolio(e.target.value)}
        />
      </label>

      <button
        className="primary-button full-button"
        onClick={buscarCita}
        disabled={loading}
      >
        {loading ? "Consultando..." : "Consultar cita"}
      </button>

      {error && (
        <div className="result-message">
          ❌ {error}
        </div>
      )}

      {cita && (
        <div className="result-card">
          <div className="result-card-header">✅ Cita encontrada</div>

          <div className="result-grid">
            <div className="result-item">
              <small>Folio</small>
              <strong>{cita.folio}</strong>
            </div>

            <div className="result-item">
              <small>Paciente</small>
              <strong>{cita.nombre}</strong>
            </div>

            <div className="result-item">
              <small>Teléfono</small>
              <strong>{cita.telefono}</strong>
            </div>

            <div className="result-item">
              <small>Especialidad</small>
              <strong>{cita.especialidad}</strong>
            </div>

            <div className="result-item">
              <small>Médico</small>
              <strong>{cita.medico}</strong>
            </div>

            <div className="result-item">
              <small>Fecha</small>
              <strong>{cita.fecha}</strong>
            </div>

            <div className="result-item">
              <small>Hora</small>
              <strong>{cita.hora}</strong>
            </div>

            <div className="result-item">
              <small>Estado</small>
              <strong>{cita.estado}</strong>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}

function DoctorsSection() {
  const [doctors, setDoctors] = useState([]);
  const [specialties, setSpecialties] = useState([]);
  const [selectedSpecialty, setSelectedSpecialty] = useState("");
  const [onlyAvailable, setOnlyAvailable] = useState(false);
  const [search, setSearch] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const loadDoctors = async () => {
      setIsLoading(true);
      setError("");

      try {
        const params = new URLSearchParams();

        if (selectedSpecialty) {
          params.set("especialidad", selectedSpecialty);
        }

        if (onlyAvailable) {
          params.set("solo_disponibles", "true");
        }

        const query = params.toString();

        const response = await fetch(
          `http://127.0.0.1:8000/api/medicos${query ? `?${query}` : ""}`
        );

        if (!response.ok) {
          throw new Error("No fue posible cargar los médicos.");
        }

        const data = await response.json();

        setDoctors(data.medicos || []);

        if (!selectedSpecialty) {
          setSpecialties(data.especialidades || []);
        }
      } catch (error) {
        console.error(error);
        setError("No fue posible conectar con el servidor.");
      } finally {
        setIsLoading(false);
      }
    };

    loadDoctors();
  }, [selectedSpecialty, onlyAvailable]);

  const filteredDoctors = doctors.filter((doctor) => {
    const searchText = search.toLowerCase().trim();

    if (!searchText) {
      return true;
    }

    return (
      doctor.nombre?.toLowerCase().includes(searchText) ||
      doctor.especialidad?.toLowerCase().includes(searchText) ||
      doctor.consultorio?.toLowerCase().includes(searchText)
    );
  });

  if (isLoading) {
    return (
      <section className="cards-grid">
        <p>Cargando médicos...</p>
      </section>
    );
  }

  if (error) {
    return (
      <section className="cards-grid">
        <p>{error}</p>
      </section>
    );
  }

  return (
    <section>
      <div className="directory-toolbar">
        <input
          type="search"
          placeholder="Buscar médico, especialidad o consultorio"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
        />

        <select
          value={selectedSpecialty}
          onChange={(event) =>
            setSelectedSpecialty(event.target.value)
          }
        >
          <option value="">Todas las especialidades</option>

          {specialties.map((specialty) => (
            <option key={specialty} value={specialty}>
              {specialty}
            </option>
          ))}
        </select>

        <label>
          <input
            type="checkbox"
            checked={onlyAvailable}
            onChange={(event) =>
              setOnlyAvailable(event.target.checked)
            }
          />
          Solo disponibles
        </label>
      </div>

      <div className="cards-grid">
        {filteredDoctors.map((doctor) => {
          const isAvailable =
            doctor.estado?.toLowerCase() === "disponible";

          return (
            <article
              className="doctor-card"
              key={doctor.id}
            >
              <div className="doctor-avatar">
                {doctor.nombre?.includes("Dra.")
                  ? "👩‍⚕️"
                  : "👨‍⚕️"}
              </div>

              <span className="specialty-badge">
                {doctor.especialidad}
              </span>

              <h3>{doctor.nombre}</h3>

              <p>
                Consultorio: <strong>{doctor.consultorio}</strong>
              </p>

              <p>
                Extensión: <strong>{doctor.telefono_interno}</strong>
              </p>

              <p>
                Estado: <strong>{doctor.estado}</strong>
              </p>

              <p>
                <a href={`mailto:${doctor.correo}`}>
                  {doctor.correo}
                </a>
              </p>

              <button
                className="outline-button"
                disabled={!isAvailable}
              >
                {isAvailable
                  ? "Ver disponibilidad"
                  : "No disponible"}
              </button>
            </article>
          );
        })}
      </div>
    </section>
  );
}

function PricesSection() {
  const [studies, setStudies] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedStudy, setSelectedStudy] = useState(null);

  useEffect(() => {
    const loadStudies = async () => {
      try {
        const response = await fetch(
          `${API_URL}/api/estudios`
        );

        if (!response.ok) {
          throw new Error("No fue posible cargar los estudios.");
        }

        const data = await response.json();

        setStudies(data.estudios || []);
      } catch (error) {
        console.error("Error al cargar estudios:", error);
        setError("No fue posible conectar con el servidor.");
      } finally {
        setIsLoading(false);
      }
    };

    loadStudies();
  }, []);

  const getStudyIcon = (study) => {
    const name = study.nombre?.toLowerCase() || "";
    const category = study.categoria?.toLowerCase() || "";

    if (name.includes("resonancia")) return "🧠";
    if (name.includes("radiografía")) return "🩻";
    if (name.includes("ultrasonido")) return "🖥️";
    if (name.includes("tomografía")) return "🔬";
    if (name.includes("electrocardiograma")) return "❤️";
    if (name.includes("orina")) return "🧴";
    if (name.includes("biometría")) return "🩸";
    if (name.includes("química")) return "🧪";

    if (category.includes("laboratorio")) return "🧪";
    if (category.includes("imagenología")) return "🩻";
    if (category.includes("cardiología")) return "❤️";

    return "🩺";
  };

  if (isLoading) {
    return (
      <section className="cards-grid">
        <p>Cargando estudios...</p>
      </section>
    );
  }

  if (error) {
    return (
      <section className="cards-grid">
        <p>{error}</p>
      </section>
    );
  }

  return (
    <>
      <section className="cards-grid">
        {studies.map((study) => (
          <article className="study-card" key={study.id}>
            <div className="study-top">
              <div className="study-icon">{getStudyIcon(study)}</div>
              <span>{study.categoria}</span>
            </div>

            <h3>{study.nombre}</h3>

            <p>Duración aproximada: {study.duracion}</p>

            <strong>{study.precio}</strong>

            <button
              className="outline-button"
              onClick={() => setSelectedStudy(study)}
            >
              Ver información
            </button>
          </article>
        ))}
      </section>

      {selectedStudy && (
        <div
          className="modal-overlay"
          onClick={() => setSelectedStudy(null)}
        >
          <div
            className="study-modal"
            onClick={(event) => event.stopPropagation()}
          >
            <button
              className="modal-close"
              onClick={() => setSelectedStudy(null)}
            >
              ×
            </button>

            <div className="modal-header">
              <div className="study-icon">
                {getStudyIcon(selectedStudy)}
              </div>

              <div>
                <span>{selectedStudy.categoria}</span>
                <h2>{selectedStudy.nombre}</h2>
              </div>
            </div>

            <div className="modal-price">
              <span>Precio</span>
              <strong>{selectedStudy.precio}</strong>
            </div>

            <div className="study-details">
              <div className="detail-item">
                <span>⏱ Duración</span>
                <strong>{selectedStudy.duracion}</strong>
              </div>

              <div className="detail-item">
                <span>🍽 Ayuno</span>
                <strong>
                  {selectedStudy.requiere_ayuno || "No disponible"}
                </strong>
              </div>

              <div className="detail-item">
                <span>⏰ Horas de ayuno</span>
                <strong>
                  {selectedStudy.horas_ayuno || "No aplica"}
                </strong>
              </div>

              <div className="detail-item">
                <span>📄 Orden médica</span>
                <strong>
                  {selectedStudy.requiere_orden_medica || "No disponible"}
                </strong>
              </div>
            </div>

            <div className="modal-section">
              <h3>📋 Preparación</h3>
              <p>
                {selectedStudy.preparacion || "No requiere preparación especial."}
              </p>
            </div>

            <div className="modal-section">
              <h3>📦 Entrega de resultados</h3>
              <p>
                {selectedStudy.entrega_resultados || "No disponible"}
              </p>
            </div>

            <div className="modal-section">
              <h3>🪪 Documentos necesarios</h3>
              <p>
                {selectedStudy.documentos_necesarios || "No disponible"}
              </p>
            </div>

            <div className="modal-section">
              <h3>💡 Recomendaciones</h3>
              <p>
                {selectedStudy.recomendaciones || "No hay recomendaciones adicionales."}
              </p>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

function FaqSection() {
  const [questions, setQuestions] = useState([]);
  const [openQuestion, setOpenQuestion] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const loadFaq = async () => {
      try {
        const response = await fetch(`${API_URL}/api/faq`);

        if (!response.ok) {
          throw new Error("No fue posible cargar las preguntas frecuentes.");
        }

        const data = await response.json();

        setQuestions(data.faq || []);
      } catch (error) {
        console.error("Error al cargar FAQ:", error);
        setError("No fue posible conectar con el servidor.");
      } finally {
        setIsLoading(false);
      }
    };

    loadFaq();
  }, []);

  const toggleQuestion = (id) => {
    setOpenQuestion((currentId) =>
      currentId === id ? null : id
    );
  };

  if (isLoading) {
    return (
      <section className="content-card">
        <p>Cargando preguntas frecuentes...</p>
      </section>
    );
  }

  if (error) {
    return (
      <section className="content-card">
        <p>{error}</p>
      </section>
    );
  }

  return (
    <section className="content-card">
      <div className="section-heading">
        <div className="section-icon">❓</div>

        <div>
          <h3>Preguntas frecuentes</h3>
          <p>Selecciona una pregunta para consultar la respuesta.</p>
        </div>
      </div>

      <div className="faq-list">
        {questions.map((item) => {
          const isOpen = openQuestion === item.id;

          return (
            <div className="faq-wrapper" key={item.id}>
              <button
                className="faq-item"
                onClick={() => toggleQuestion(item.id)}
              >
                <div>
                  <small>{item.categoria}</small>
                  <span>{item.pregunta}</span>
                </div>

                <strong>{isOpen ? "−" : "＋"}</strong>
              </button>

              {isOpen && (
                <div className="faq-answer">
                  <p>{item.respuesta}</p>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </section>
  );
}

function InformationSection() {
  const [activeTab, setActiveTab] = useState("privacidad");

  const tabs = [
    {
      id: "privacidad",
      icon: "🔒",
      label: "Privacidad",
    },
    {
      id: "cancelaciones",
      icon: "📅",
      label: "Cancelaciones",
    },
    {
      id: "convenios",
      icon: "🏥",
      label: "Convenios",
    },
    {
      id: "consulta",
      icon: "🩺",
      label: "Pre y post consulta",
    },
  ];

  return (
    <section className="patient-info-page">
      <div className="patient-info-hero">
        <div>
          <span className="patient-info-badge">
            Centro de orientación
          </span>

          <h3>Información para pacientes</h3>

          <p>
            Consulta las políticas demostrativas, condiciones de citas,
            convenios simulados e indicaciones generales de MediAssist.
          </p>
        </div>

        <div className="patient-info-hero-icon">📚</div>
      </div>

      <div className="patient-info-layout">
        <aside className="patient-info-navigation">
          <span className="patient-info-navigation-title">
            Selecciona un tema
          </span>

          <div className="patient-info-tabs">
            {tabs.map((tab) => (
              <button
                type="button"
                key={tab.id}
                className={
                  activeTab === tab.id ? "active" : ""
                }
                onClick={() => setActiveTab(tab.id)}
              >
                <span>{tab.icon}</span>

                <div>
                  <strong>{tab.label}</strong>
                  <small>Consultar información</small>
                </div>

                <b>›</b>
              </button>
            ))}
          </div>
        </aside>

        <main className="patient-info-content">
          {activeTab === "privacidad" && <PrivacyInformation />}

          {activeTab === "cancelaciones" && (
            <CancellationInformation />
          )}

          {activeTab === "convenios" && <CoverageInformation />}

          {activeTab === "consulta" && <ConsultationInformation />}
        </main>
      </div>
    </section>
  );
}

function PrivacyInformation() {
  return (
    <article className="patient-topic">
      <div className="patient-topic-header">
        <div className="patient-topic-icon">🔒</div>

        <div>
          <span>Protección de información</span>
          <h2>Política de privacidad del paciente</h2>
          <p>
            Conoce qué datos utiliza MediAssist durante el registro y
            consulta de citas.
          </p>
        </div>
      </div>

      <div className="patient-highlight">
        <span>🛡️</span>

        <div>
          <strong>Compromiso de privacidad</strong>
          <p>
            MediAssist utiliza los datos registrados únicamente para
            demostrar la administración de citas y la consulta de
            información dentro de este proyecto académico.
          </p>
        </div>
      </div>

      <div className="patient-cards-grid">
        <section className="patient-detail-card">
          <div className="patient-card-heading">
            <span>📋</span>
            <h3>Datos registrados</h3>
          </div>

          <p>
            Para generar una cita, el sistema puede solicitar:
          </p>

          <ul className="patient-check-list">
            <li>Nombre completo del paciente.</li>
            <li>Número telefónico de contacto.</li>
            <li>Especialidad seleccionada.</li>
            <li>Nombre del médico.</li>
            <li>Fecha y hora de atención.</li>
            <li>Folio generado por el sistema.</li>
          </ul>
        </section>

        <section className="patient-detail-card">
          <div className="patient-card-heading">
            <span>⚙️</span>
            <h3>Uso de la información</h3>
          </div>

          <p>
            Los datos permiten realizar las siguientes funciones:
          </p>

          <ul className="patient-check-list">
            <li>Registrar una nueva cita médica.</li>
            <li>Asignar médico y especialidad.</li>
            <li>Consultar una cita mediante folio.</li>
            <li>Mostrar la fecha y hora programadas.</li>
            <li>Organizar la información de la demostración.</li>
          </ul>
        </section>

        <section className="patient-detail-card">
          <div className="patient-card-heading">
            <span>👁️</span>
            <h3>Acceso a los datos</h3>
          </div>

          <p>
            La información se visualiza únicamente dentro de MediAssist
            durante la ejecución del proyecto.
          </p>

          <ul className="patient-check-list">
            <li>No se comercializa la información.</li>
            <li>No se utiliza para publicidad.</li>
            <li>No debe contener datos médicos reales.</li>
            <li>Solo se utiliza con fines demostrativos.</li>
          </ul>
        </section>

        <section className="patient-detail-card">
          <div className="patient-card-heading">
            <span>📝</span>
            <h3>Recomendación de uso</h3>
          </div>

          <p>
            Para realizar pruebas, utiliza nombres, teléfonos y datos
            ficticios.
          </p>

          <ul className="patient-check-list">
            <li>Evita registrar diagnósticos reales.</li>
            <li>No ingreses información clínica sensible.</li>
            <li>Utiliza números telefónicos simulados.</li>
            <li>Conserva el folio para probar la consulta.</li>
          </ul>
        </section>
      </div>

    </article>
  );
}

function CancellationInformation() {
  return (
    <article className="patient-topic">
      <div className="patient-topic-header">
        <div className="patient-topic-icon">📅</div>

        <div>
          <span>Administración de citas</span>
          <h2>Cancelaciones y reagendamiento</h2>
          <p>
            Consulta las condiciones para cambiar o cancelar una cita
            registrada en MediAssist.
          </p>
        </div>
      </div>

      <div className="patient-process-grid">
        <section className="patient-process-card">
          <span className="patient-process-number">01</span>
          <div className="patient-process-icon">❌</div>
          <h3>Cancelar una cita</h3>
          <p>
            La cancelación puede solicitarse hasta 24 horas antes de la
            fecha y hora programadas.
          </p>
        </section>

        <section className="patient-process-card">
          <span className="patient-process-number">02</span>
          <div className="patient-process-icon">🔄</div>
          <h3>Reagendar una cita</h3>
          <p>
            El paciente puede solicitar una nueva fecha, hora o médico,
            siempre que exista disponibilidad.
          </p>
        </section>

        <section className="patient-process-card">
          <span className="patient-process-number">03</span>
          <div className="patient-process-icon">⏰</div>
          <h3>Llegadas tardías</h3>
          <p>
            Si el paciente llega con más de 15 minutos de retraso, la
            atención dependerá de la disponibilidad del médico.
          </p>
        </section>
      </div>

      <section className="patient-wide-card">
        <div className="patient-card-heading">
          <span>🔎</span>
          <h3>Datos necesarios para solicitar un cambio</h3>
        </div>

        <div className="patient-data-row">
          <div>
            <small>Identificación de la cita</small>
            <strong>Folio</strong>
          </div>

          <div>
            <small>Datos del paciente</small>
            <strong>Nombre completo</strong>
          </div>

          <div>
            <small>Modificación</small>
            <strong>Fecha, hora o médico</strong>
          </div>
        </div>
      </section>

      <div className="patient-cards-grid two-columns">
        <section className="patient-detail-card">
          <div className="patient-card-heading">
            <span>✅</span>
            <h3>Cambios disponibles</h3>
          </div>

          <ul className="patient-check-list">
            <li>Cambiar la fecha de la consulta.</li>
            <li>Seleccionar otro horario.</li>
            <li>Cambiar al médico asignado.</li>
            <li>Elegir una especialidad diferente.</li>
          </ul>
        </section>

        <section className="patient-detail-card">
          <div className="patient-card-heading">
            <span>📌</span>
            <h3>Condiciones importantes</h3>
          </div>

          <ul className="patient-check-list">
            <li>Los cambios dependen de la disponibilidad.</li>
            <li>El paciente debe conservar su folio.</li>
            <li>La nueva cita debe confirmarse nuevamente.</li>
            <li>Los horarios pueden variar según el médico.</li>
          </ul>
        </section>
      </div>

      <div className="patient-highlight">
        <span>ℹ️</span>

        <div>
          <strong>Conserva tu folio</strong>

          <p>
            El folio permite localizar rápidamente la cita y consultar
            el médico, la especialidad, la fecha y el horario registrados.
          </p>
        </div>
      </div>
    </article>
  );
}

function CoverageInformation() {
  const agreements = [
    {
      name: "Salud Integral Plus",
      type: "Convenio general",
      coverage: "Consultas y estudios básicos",
      icon: "➕",
    },
    {
      name: "VidaCare",
      type: "Plan familiar",
      coverage: "Consultas de especialidad",
      icon: "💙",
    },
    {
      name: "Medical Protect",
      type: "Cobertura empresarial",
      coverage: "Consultas y diagnóstico",
      icon: "🛡️",
    },
    {
      name: "Bienestar Familiar",
      type: "Plan preventivo",
      coverage: "Medicina general y laboratorio",
      icon: "👨‍👩‍👧",
    },
  ];

  return (
    <article className="patient-topic">
      <div className="patient-topic-header">
        <div className="patient-topic-icon">🏥</div>

        <div>
          <span>Planes demostrativos</span>
          <h2>Convenios y coberturas médicas</h2>
          <p>
            Ejemplos ficticios de planes que podrían utilizarse dentro
            de un portal hospitalario.
          </p>
        </div>
      </div>

      <div className="agreement-grid">
        {agreements.map((agreement) => (
          <section className="agreement-card" key={agreement.name}>
            <div className="agreement-icon">{agreement.icon}</div>

            <span>{agreement.type}</span>
            <h3>{agreement.name}</h3>
            <p>{agreement.coverage}</p>

            <div className="agreement-status">
              <span></span>
              Convenio de demostración
            </div>
          </section>
        ))}
      </div>

      <section className="patient-wide-card">
        <div className="patient-card-heading">
          <span>🩺</span>
          <h3>Servicios que podrían incluirse</h3>
        </div>

        <div className="coverage-services">
          <div>
            <span>👨‍⚕️</span>
            <strong>Consulta general</strong>
          </div>

          <div>
            <span>🧑‍⚕️</span>
            <strong>Especialistas</strong>
          </div>

          <div>
            <span>🧪</span>
            <strong>Laboratorio</strong>
          </div>

          <div>
            <span>🩻</span>
            <strong>Rayos X</strong>
          </div>

          <div>
            <span>🔬</span>
            <strong>Ultrasonido</strong>
          </div>

          <div>
            <span>🧲</span>
            <strong>Resonancia</strong>
          </div>

          <div>
            <span>🖥️</span>
            <strong>Tomografía</strong>
          </div>

          <div>
            <span>📄</span>
            <strong>Resultados</strong>
          </div>
        </div>
      </section>

      <div className="patient-cards-grid two-columns">
        <section className="patient-detail-card">
          <div className="patient-card-heading">
            <span>📋</span>
            <h3>Validación simulada</h3>
          </div>

          <ul className="patient-check-list">
            <li>Seleccionar el convenio.</li>
            <li>Confirmar la especialidad.</li>
            <li>Consultar el estudio solicitado.</li>
            <li>Revisar el porcentaje de cobertura.</li>
          </ul>
        </section>

        <section className="patient-detail-card">
          <div className="patient-card-heading">
            <span>💳</span>
            <h3>Información de pago</h3>
          </div>

          <ul className="patient-check-list">
            <li>La cobertura puede ser parcial o total.</li>
            <li>Algunos servicios pueden requerir copago.</li>
            <li>Los precios se consultan en MediAssist.</li>
            <li>No se procesan pagos dentro del proyecto.</li>
          </ul>
        </section>
      </div>
    </article>
  );
}

function ConsultationInformation() {
  return (
    <article className="patient-topic">
      <div className="patient-topic-header">
        <div className="patient-topic-icon">🩺</div>

        <div>
          <span>Orientación general</span>
          <h2>Instrucciones pre y post consulta</h2>
          <p>
            Recomendaciones generales para preparar una consulta y dar
            seguimiento a las indicaciones médicas.
          </p>
        </div>
      </div>

      <div className="consultation-columns">
        <section className="consultation-column before">
          <div className="consultation-column-header">
            <div>01</div>

            <span>
              <small>Preparación</small>
              <strong>Antes de la consulta</strong>
            </span>
          </div>

          <ul className="consultation-list">
            <li>
              <span>⏰</span>
              <div>
                <strong>Llegar con anticipación</strong>
                <p>
                  Se recomienda llegar 20 minutos antes del horario
                  registrado.
                </p>
              </div>
            </li>

            <li>
              <span>🔎</span>
              <div>
                <strong>Tener disponible el folio</strong>
                <p>
                  El folio permite consultar los datos principales de
                  la cita.
                </p>
              </div>
            </li>

            <li>
              <span>📄</span>
              <div>
                <strong>Llevar estudios anteriores</strong>
                <p>
                  Presenta resultados previos cuando puedan servir como
                  referencia.
                </p>
              </div>
            </li>

            <li>
              <span>💊</span>
              <div>
                <strong>Preparar información relevante</strong>
                <p>
                  Anota medicamentos, alergias y antecedentes que
                  quieras comentar.
                </p>
              </div>
            </li>
          </ul>
        </section>

        <section className="consultation-column after">
          <div className="consultation-column-header">
            <div>02</div>

            <span>
              <small>Seguimiento</small>
              <strong>Después de la consulta</strong>
            </span>
          </div>

          <ul className="consultation-list">
            <li>
              <span>✅</span>
              <div>
                <strong>Revisar las indicaciones</strong>
                <p>
                  Confirma que comprendes las recomendaciones recibidas.
                </p>
              </div>
            </li>

            <li>
              <span>📝</span>
              <div>
                <strong>Conservar documentos</strong>
                <p>
                  Guarda recetas, órdenes y resultados relacionados con
                  la consulta.
                </p>
              </div>
            </li>

            <li>
              <span>🧪</span>
              <div>
                <strong>Consultar estudios</strong>
                <p>
                  Revisa en MediAssist el precio, preparación y duración
                  del estudio solicitado.
                </p>
              </div>
            </li>

            <li>
              <span>📅</span>
              <div>
                <strong>Agendar seguimiento</strong>
                <p>
                  Registra una nueva cita cuando el médico recomiende
                  una revisión posterior.
                </p>
              </div>
            </li>
          </ul>
        </section>
      </div>

      <section className="patient-wide-card">
        <div className="patient-card-heading">
          <span>🧪</span>
          <h3>Información disponible sobre estudios</h3>
        </div>

        <div className="patient-data-row four-items">
          <div>
            <small>Consulta</small>
            <strong>Precio</strong>
          </div>

          <div>
            <small>Indicaciones</small>
            <strong>Preparación</strong>
          </div>

          <div>
            <small>Tiempo</small>
            <strong>Duración</strong>
          </div>

          <div>
            <small>Resultados</small>
            <strong>Entrega estimada</strong>
          </div>
        </div>
      </section>

    </article>
  );
}

export default App;