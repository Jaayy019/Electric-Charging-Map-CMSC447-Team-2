import { useState, useEffect } from "react";


const styles = {

  page: {
    backgroundColor: "#1a6fd4",
    minHeight: "100vh",
    width: "100vw",
    fontFamily: "'Inter', 'Open Sans', sans-serif",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    padding: "32px 16px",
    boxSizing: "border-box",
  },

  // Top bar with back button and title
  header: {
    width: "100%",
    maxWidth: "480px",
    display: "flex",
    alignItems: "center",
    gap: "12px",
    marginBottom: "24px",
  },

  // Back to map button
  backBtn: {
    background: "rgba(255,255,255,0.2)",
    border: "none",
    borderRadius: "8px",
    color: "white",
    fontSize: "14px",
    fontWeight: "500",
    padding: "8px 14px",
    cursor: "pointer",
  },

  // "My Vehicles" heading
  headerTitle: {
    fontSize: "22px",
    fontWeight: "700",
    color: "white",
    margin: 0,
  },

  // White card used for both the form and each vehicle entry
  card: {
    backgroundColor: "white",
    borderRadius: "14px",
    padding: "22px 24px",
    width: "100%",
    maxWidth: "480px",
    boxSizing: "border-box",
    marginBottom: "16px",
  },

  // Section title inside a card
  cardTitle: {
    fontSize: "16px",
    fontWeight: "600",
    color: "#111",
    margin: "0 0 16px",
  },

  // Two-column grid for form fields
  formGrid: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: "12px",
    marginBottom: "16px",
  },

  // Wrapper for a single label + input/select pair
  fieldGroup: {
    display: "flex",
    flexDirection: "column",
    gap: "4px",
  },

  // Field label text
  label: {
    fontSize: "12px",
    fontWeight: "500",
    color: "#555",
  },

  // Number/text input
  input: {
    height: "36px",
    border: "1px solid #ddd",
    borderRadius: "8px",
    padding: "0 10px",
    fontSize: "14px",
    color: "#111",
    backgroundColor: "#fafafa",
    outline: "none",
    boxSizing: "border-box",
    width: "100%",
  },

  // Active dropdown select
  select: {
    height: "36px",
    border: "1px solid #ddd",
    borderRadius: "8px",
    padding: "0 10px",
    fontSize: "14px",
    color: "#111",
    backgroundColor: "#fafafa",
    outline: "none",
    boxSizing: "border-box",
    width: "100%",
    cursor: "pointer",
  },

  // Greyed out while disabled (model dropdown before make is chosen)
  selectDisabled: {
    height: "36px",
    border: "1px solid #ddd",
    borderRadius: "8px",
    padding: "0 10px",
    fontSize: "14px",
    color: "#aaa",
    backgroundColor: "#f0f0f0",
    outline: "none",
    boxSizing: "border-box",
    width: "100%",
    cursor: "not-allowed",
  },

  // Primary submit button
  btnPrimary: {
    width: "100%",
    height: "40px",
    backgroundColor: "#1a6fd4",
    color: "white",
    border: "none",
    borderRadius: "8px",
    fontSize: "14px",
    fontWeight: "600",
    cursor: "pointer",
  },

  // Greyed out while POST is in flight
  btnDisabled: {
    width: "100%",
    height: "40px",
    backgroundColor: "#a0c4f1",
    color: "white",
    border: "none",
    borderRadius: "8px",
    fontSize: "14px",
    fontWeight: "600",
    cursor: "not-allowed",
  },

  // Inline error text
  error: {
    fontSize: "13px",
    color: "#c0392b",
    margin: "0 0 10px",
  },

  // Inline success text
  success: {
    fontSize: "13px",
    color: "#27ae60",
    margin: "0 0 10px",
  },

  // Row inside a saved vehicle card
  vehicleRow: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "flex-start",
  },

  vehicleName: {
    fontSize: "15px",
    fontWeight: "600",
    color: "#111",
    margin: "0 0 4px",
  },

  // Port type shown as subtitle
  vehicleSub: {
    fontSize: "13px",
    color: "#777",
    margin: 0,
  },

  // Red remove button per vehicle
  deleteBtn: {
    background: "none",
    border: "1px solid #f5c2c2",
    borderRadius: "7px",
    color: "#c0392b",
    fontSize: "12px",
    fontWeight: "500",
    padding: "5px 10px",
    cursor: "pointer",
    whiteSpace: "nowrap",
  },

  // Shown when user has no vehicles yet
  emptyText: {
    fontSize: "14px",
    color: "#999",
    textAlign: "center",
    padding: "10px 0",
    margin: 0,
  },

  // Small hint under a loading dropdown
  loadingHint: {
    fontSize: "11px",
    color: "#aaa",
    margin: "2px 0 0",
  },

  // Green badge when port type was auto-detected
  autoBadge: {
    fontSize: "11px",
    backgroundColor: "#e8f5e9",
    color: "#2e7d32",
    borderRadius: "4px",
    padding: "2px 6px",
    marginTop: "4px",
    display: "inline-block",
  },
};

const EV_MAKES = [
  "Audi", "BMW", "Cadillac", "Chevrolet", "Chrysler",
  "Ford", "GMC", "Honda", "Hyundai", "Jaguar",
  "Jeep", "Kia", "Land Rover", "Lucid", "Mazda",
  "Mercedes-Benz", "MINI", "Nissan", "Polestar", "Porsche",
  "Rivian", "Subaru", "Tesla", "Toyota", "Volkswagen", "Volvo",
];

// Common EV connector types for the port type dropdown
const PORT_TYPES = [
  "CCS (Type 1)",
  "CCS (Type 2)",
  "CHAdeMO",
  "Type 1 (J1772)",
  "Type 2 (Mennekes)",
  "Tesla (NACS)",
  "Nema 14-50",
  "Nema 5-15",
];

function mapPlugType(plug) {
  if (!plug) return null;
  const p = plug.toLowerCase();
  if (p.includes("ccs") && p.includes("2"))           return "CCS (Type 2)";
  if (p.includes("ccs") && p.includes("1"))           return "CCS (Type 1)";
  if (p === "ccs")                                     return "CCS (Type 1)"; // default CCS to Type 1
  if (p.includes("chademo"))                           return "CHAdeMO";
  if (p.includes("j1772") || p.includes("type 1"))    return "Type 1 (J1772)";
  if (p.includes("type 2") || p.includes("mennekes")) return "Type 2 (Mennekes)";
  if (p.includes("tesla") || p.includes("nacs"))      return "Tesla (NACS)";
  if (p.includes("nema 14"))                           return "Nema 14-50";
  if (p.includes("nema 5"))                            return "Nema 5-15";
  return null;
}

// All vehicle API calls use /api/auth/me/vehicles - the session cookie identifies
// the user automatically, so no user ID is needed in the frontend.

export default function VehicleManager({ user, goToMap }) {

  // Saved vehicles fetched from the backend
  const [vehicles, setVehicles] = useState([]);
  const [make, setMake] = useState("");

  // Models fetched from NHTSA
  const [models, setModels] = useState([]);
  const [modelsLoading, setModelsLoading] = useState(false);
  const [model, setModel] = useState("");

  // Year and port type
  const [year, setYear] = useState("");
  const [portType, setPortType] = useState(PORT_TYPES[0]);
  const [portAutoFilled, setPortAutoFilled] = useState(false);

  // UI state
  const [loading, setLoading] = useState(true);   
  const [saving, setSaving] = useState(false);    
  const [error, setError] = useState("");
  const [successMsg, setSuccessMsg] = useState("");

  // Fetch saved vehicles
  useEffect(() => {

    fetchVehicles();

  }, []);

  async function fetchVehicles() {

    setLoading(true);

    try {

      // Session cookie
      const res = await fetch("/api/auth/me/vehicles", {

        credentials: "include", 

      });

      if (res.ok) {

        setVehicles(await res.json());

      } 
      
      else {

        setError("Could not load vehicles.");

      }

    } catch {

      setError("Network error loading vehicles.");

    } finally {

      setLoading(false);

    }

  }

  // Fetches models for the chosen make from NHTSA
  async function handleMakeChange(e) {

    const selectedMake = e.target.value;
    setMake(selectedMake);
    setModel("");
    setModels([]);
    setPortAutoFilled(false);

    if (!selectedMake) return;

    setModelsLoading(true);

    try {

      const res = await fetch(

        `/api/vehicle/vehicles/models/${encodeURIComponent(selectedMake)}`

      );

      if (res.ok) {

        const data = await res.json();

        // NHTSA returns
        const modelList = Array.isArray(data?.Results)

          ? data.Results.map((m) => m.Model_Name).filter(Boolean).sort()

          : [];

        setModels(modelList);

      } 
      
      else {

        setError("Could not load models for this make.");
      }

    } catch {

      setError("Network error loading models.");

    } finally {

      setModelsLoading(false);

    }
  }

  // After model is picked, calls /api/vehicle/electric-vehicles
  // to get EV specs and auto-fill the port type
  async function handleModelChange(e) {

    const selectedModel = e.target.value;
    setModel(selectedModel);
    setPortAutoFilled(false);

    if (!selectedModel || !make) return;

    try {

      const res = await fetch(

        `/api/vehicle/electric-vehicles?make=${encodeURIComponent(make.toLowerCase())}&model=${encodeURIComponent(selectedModel.toLowerCase())}`

      );

      if (res.ok) {

        const data = await res.json();

        if (Array.isArray(data) && data.length > 0) {

          const chargePort = data[0].charge_port;

          if (chargePort) {

            const mapped = mapPlugType(chargePort);

            if (mapped) {

              setPortType(mapped);
              setPortAutoFilled(true);

            }

          }

        }

      }

    } catch {

    }

  }

  // Add vehicle 
  async function handleAdd(e) {

    e.preventDefault();
    setError("");
    setSuccessMsg("");
    setSaving(true);

    try {
      
      const res = await fetch("/api/auth/me/vehicles", {

        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },

        body: JSON.stringify({

          make,
          model,
          year: parseInt(year, 10),  // backend expects integer
          port_type: portType,

        }),

      });

      if (res.ok) {

        // Reset the form
        setMake("");
        setModel("");
        setModels([]);
        setYear("");
        setPortType(PORT_TYPES[0]);
        setPortAutoFilled(false);
        setSuccessMsg("Vehicle added!");
        await fetchVehicles();  // refresh the list

      } 
      
      else {

        const data = await res.json().catch(() => ({}));
        setError(data.detail || "Failed to add vehicle.");

      }

    } catch {

      setError("Network error. Is the backend running?");

    } finally {

      setSaving(false);

    }

  }

  // Delete vehicle 
  async function handleDelete(vehicleId) {

    try {

      const res = await fetch(`/api/auth/me/vehicles/${vehicleId}`, {

        method: "DELETE",
        credentials: "include",

      });

      if (res.ok || res.status === 204) {

        // Remove from local state immediately — no re-fetch needed
        setVehicles((prev) => prev.filter((v) => v.id !== vehicleId));

      } 
      
      else {

        setError("Failed to delete vehicle.");

      }

    } catch {
      setError("Network error deleting vehicle.");
    }

  }

  return (

    <div style={styles.page}>

      {/* Header - back button + page title */}
      <div style={styles.header}>

        <button style={styles.backBtn} onClick={goToMap}>← Map</button>
        <h1 style={styles.headerTitle}>My Vehicles</h1>

      </div>

      {/* Add Vehicle Form */}

      <div style={styles.card}>

        <p style={styles.cardTitle}>Add a Vehicle</p>

        <form onSubmit={handleAdd}>

          <div style={styles.formGrid}>

            {/* Make */}
            <div style={styles.fieldGroup}>

              <label style={styles.label}>Make</label>

              <select
                style={styles.select}
                value={make}
                onChange={handleMakeChange}
                required
              >

                <option value="">Select make...</option>

                {EV_MAKES.map((m) => (
                  <option key={m} value={m}>{m}</option>
                ))}

              </select>

            </div>

            <div style={styles.fieldGroup}>

              <label style={styles.label}>Model</label>

              <select
                style={!make || modelsLoading ? styles.selectDisabled : styles.select}
                value={model}
                onChange={handleModelChange}
                disabled={!make || modelsLoading}
                required
              >

                <option value="">
                  {modelsLoading
                    ? "Loading..."
                    : !make
                    ? "Select make first"
                    : "Select model..."}
                </option>

                {models.map((m) => (
                  <option key={m} value={m}>{m}</option>
                ))}

              </select>

              {modelsLoading && (

                <span style={styles.loadingHint}>Fetching models...</span>

              )}

            </div>

            {/* Year */}

            <div style={styles.fieldGroup}>

              <label style={styles.label}>Year</label>

              <input
                style={styles.input}
                type="number"
                placeholder="e.g. 2022"
                value={year}
                onChange={(e) => setYear(e.target.value)}
                min="1990"
                max="2030"
                required
              />

            </div>

            {/* Port type - auto-filled when model selected, can be overridden */}
            <div style={styles.fieldGroup}>

              <label style={styles.label}>Port Type</label>

              <select
                style={styles.select}
                value={portType}
                onChange={(e) => {
                  setPortType(e.target.value);
                  setPortAutoFilled(false); // clear badge if user overrides
                }}
              >

                {PORT_TYPES.map((p) => (

                  <option key={p} value={p}>{p}</option>

                ))}

              </select>

              {/* Green badge shown when port type was auto-detected from API Ninjas */}
              {portAutoFilled && (

                <span style={styles.autoBadge}>✓ Auto-detected</span>

              )}

            </div>

          </div>

          {/* Inline feedback */}
          {error && <p style={styles.error}>{error}</p>}
          {successMsg && <p style={styles.success}>{successMsg}</p>}

          <button

            type="submit"
            style={saving ? styles.btnDisabled : styles.btnPrimary}
            disabled={saving}

          >
            {saving ? "Adding..." : "Add Vehicle"}

          </button>

        </form>

      </div>

      <div style={{ width: "100%", maxWidth: "480px" }}>

        {/* Vehicle count */}
        <p style={{ color: "rgba(255,255,255,0.75)", fontSize: "13px", margin: "0 0 10px 4px" }}>

          {vehicles.length} vehicle{vehicles.length !== 1 ? "s" : ""} saved

        </p>

        {/* Loading state */}
        {loading && (

          <p style={{ fontSize: "14px", color: "rgba(255,255,255,0.8)", textAlign: "center" }}>

            Loading vehicles...

          </p>

        )}

        {/* Empty state */}
        {!loading && vehicles.length === 0 && (

          <div style={styles.card}>

            <p style={styles.emptyText}>No vehicles added yet. Add one above!</p>

          </div>

        )}

        {/* One card per saved vehicle */}
        {vehicles.map((v) => (

          <div key={v.id} style={styles.card}>

            <div style={styles.vehicleRow}>

              <div>

                <p style={styles.vehicleName}>{v.year} {v.make} {v.model}</p>
                <p style={styles.vehicleSub}>{v.port_type}</p>

              </div>

              <button style={styles.deleteBtn} onClick={() => handleDelete(v.id)}>

                Remove

              </button>

            </div>

          </div>

        ))}

      </div>

    </div>

  );

}