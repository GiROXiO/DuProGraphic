import { useState, useEffect } from "react";
import axios from "axios";
import Navbar from "./Navbar";
import { Briefcase } from "lucide-react";

export default function Jobs() {
  const [ofertas, setOfertas] = useState([]);
  const [loading, setLoading] = useState(true);
  const user = JSON.parse(localStorage.getItem("duprographic_user"));

  useEffect(() => {
    const fetchJobs = async () => {
      try {
        // Llama a tu función de recomendación de Neo4j a través de FastAPI
        const response = await axios.get(
          `http://localhost:8000/api/users/${user.entidad_id}/feed/jobs`,
        );
        setOfertas(response.data.data);
      } catch (error) {
        console.error("Error cargando ofertas:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchJobs();
  }, [user.entidad_id]);

  return (
    <div className="min-h-screen bg-[#f3f2ef]">
      <Navbar />
      <main className="max-w-4xl mx-auto px-4 pt-20">
        <div className="bg-white rounded-lg shadow border border-gray-200 p-6 mb-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">
            Recomendado para ti
          </h2>
          <p className="text-sm text-gray-500 mb-6">
            Basado en tu perfil, habilidades ({user.rol}) y distancia en el
            grafo.
          </p>

          {loading ? (
            <div className="text-center py-8 text-gray-500">
              Buscando oportunidades en Neo4j...
            </div>
          ) : (
            <div className="space-y-4">
              {ofertas.map((oferta) => (
                <div
                  key={oferta.id}
                  className="border-b border-gray-100 pb-4 last:border-0 flex items-start space-x-4"
                >
                  <div className="h-12 w-12 bg-gray-100 rounded flex items-center justify-center text-gray-500 flex-shrink-0">
                    <Briefcase className="h-6 w-6" />
                  </div>
                  <div className="flex-1">
                    <h3 className="text-base font-bold text-[#0a66c2] hover:underline cursor-pointer">
                      {oferta.titulo}
                    </h3>
                    <p className="text-sm text-gray-900">{oferta.empresa}</p>
                    <p className="text-xs text-gray-500 mt-1">
                      {oferta.modalidad} · {oferta.experiencia}
                    </p>
                    {/* Renderiza las habilidades coincidentes de Neo4j */}
                    <div className="mt-2 flex flex-wrap gap-2">
                      {oferta.habilidades?.slice(0, 3).map((hab, idx) => (
                        <span
                          key={idx}
                          className="bg-green-50 text-green-700 text-xs px-2 py-1 rounded-full font-medium"
                        >
                          ✓ {hab}
                        </span>
                      ))}
                    </div>
                  </div>
                  <button className="px-4 py-1.5 border border-[#0a66c2] text-[#0a66c2] rounded-full text-sm font-bold hover:bg-blue-50 transition-colors">
                    Postular
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
