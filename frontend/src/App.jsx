import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";
import Login from "./components/main_views/Login";
import Feed from "./components/main_views/Feed";

// Placeholder del Feed que construiremos en el siguiente bloque
function Feed() {
  const user = JSON.parse(localStorage.getItem("duprographic_user"));

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="min-h-screen bg-[#f3f2ef] flex flex-col items-center pt-20">
      <h1 className="text-3xl font-bold text-gray-800">
        Bienvenido, {user.nombre}
      </h1>
      <p className="text-gray-600 mt-2">Sesión iniciada como: {user.rol}</p>
      <button
        onClick={() => {
          localStorage.removeItem("duprographic_user");
          window.location.reload();
        }}
        className="mt-6 px-4 py-2 border border-[#0a66c2] text-[#0a66c2] rounded-full hover:bg-blue-50 font-semibold transition-colors"
      >
        Cerrar sesión
      </button>
    </div>
  );
}

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<Feed />} />
      </Routes>
    </Router>
  );
}

export default App;
