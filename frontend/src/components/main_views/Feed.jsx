import { Navigate } from "react-router-dom";
import Navbar from "./Navbar";

export default function Feed() {
  const user = JSON.parse(localStorage.getItem("duprographic_user"));

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="min-h-screen bg-[#f3f2ef]">
      <Navbar />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {/* Columna Izquierda: Tarjeta de Perfil */}
          <div className="col-span-1">
            <div className="bg-white rounded-lg shadow border border-gray-200 overflow-hidden">
              <div className="h-16 bg-gradient-to-r from-gray-300 to-gray-200"></div>
              <div className="px-4 pb-4">
                <div className="relative -mt-10 mb-2 flex justify-center">
                  <div className="h-16 w-16 bg-white rounded-full p-1">
                    <div className="h-full w-full bg-[#0a66c2] rounded-full flex items-center justify-center text-white font-bold text-xl">
                      {user.nombre.charAt(0).toUpperCase()}
                    </div>
                  </div>
                </div>
                <div className="text-center">
                  <h2 className="text-base font-bold text-gray-900 hover:underline cursor-pointer">
                    {user.nombre}
                  </h2>
                  <p className="text-xs text-gray-500 mt-1 capitalize">
                    {user.rol}
                  </p>
                </div>
                <div className="mt-4 pt-4 border-t border-gray-100">
                  <div className="flex justify-between items-center text-xs mb-2 cursor-pointer hover:bg-gray-50 p-1">
                    <span className="text-gray-500">Contactos</span>
                    <span className="text-[#0a66c2] font-bold">0</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Columna Central: Muro principal (Feed) */}
          <div className="col-span-1 md:col-span-2 space-y-4">
            {/* Caja para crear publicación */}
            <div className="bg-white rounded-lg shadow border border-gray-200 p-4">
              <div className="flex items-center space-x-3">
                <div className="h-10 w-10 bg-[#0a66c2] rounded-full flex items-center justify-center text-white font-bold flex-shrink-0">
                  {user.nombre.charAt(0).toUpperCase()}
                </div>
                <button className="flex-1 text-left bg-white border border-gray-400 text-gray-500 rounded-full px-4 py-3 text-sm font-medium hover:bg-gray-100 transition-colors">
                  Crear publicación...
                </button>
              </div>
            </div>

            {/* Divisor / Orden */}
            <div className="flex items-center text-xs text-gray-500">
              <hr className="flex-1 border-gray-300" />
              <span className="mx-2">Ofertas y actividad reciente</span>
              <hr className="flex-1 border-gray-300" />
            </div>

            {/* Espacio para renderizar las tarjetas desde la API */}
            <div className="bg-white rounded-lg shadow border border-gray-200 p-8 text-center text-gray-500">
              Cargando el feed desde Neo4j...
            </div>
          </div>

          {/* Columna Derecha: Recomendaciones */}
          <div className="col-span-1 hidden md:block">
            <div className="bg-white rounded-lg shadow border border-gray-200 p-4">
              <h2 className="text-sm font-bold text-gray-900 mb-4">
                Añadir a tu feed
              </h2>
              <div className="space-y-4">
                <div className="flex items-start space-x-3">
                  <div className="h-10 w-10 bg-gray-200 rounded-full flex-shrink-0"></div>
                  <div>
                    <h3 className="text-sm font-bold text-gray-900">
                      Universidad del Norte
                    </h3>
                    <p className="text-xs text-gray-500">
                      Institución educativa
                    </p>
                    <button className="mt-1 px-4 py-1 border border-gray-500 text-gray-600 rounded-full text-sm font-medium hover:bg-gray-100 hover:border-gray-700 transition-colors">
                      + Seguir
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
