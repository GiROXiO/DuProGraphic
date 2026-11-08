import {
  Search,
  Home,
  Users,
  Briefcase,
  MessageSquare,
  Bell,
  LogOut,
} from "lucide-react";
import { useNavigate } from "react-router-dom";

export default function Navbar() {
  const navigate = useNavigate();
  const user = JSON.parse(localStorage.getItem("duprographic_user"));

  const handleLogout = () => {
    localStorage.removeItem("duprographic_user");
    navigate("/login");
  };

  return (
    <nav className="bg-white border-b border-gray-200 fixed w-full z-50 top-0">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-14">
          <div className="flex items-center">
            <div className="flex-shrink-0 flex items-center bg-[#0a66c2] text-white font-bold px-2 py-1 rounded">
              DG
            </div>
            <div className="hidden md:ml-4 md:flex items-center">
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Search className="h-4 w-4 text-gray-500" />
                </div>
                <input
                  type="text"
                  placeholder="Buscar"
                  className="bg-[#eef3f8] border-none rounded-md py-1.5 pl-10 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-[#0a66c2] w-64"
                />
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-6">
            <button className="flex flex-col items-center text-gray-900 border-b-2 border-black pb-1">
              <Home className="h-5 w-5" />
              <span className="text-[11px] hidden md:block">Inicio</span>
            </button>
            <button className="flex flex-col items-center text-gray-500 hover:text-gray-900 transition-colors">
              <Users className="h-5 w-5" />
              <span className="text-[11px] hidden md:block">Mi red</span>
            </button>
            <button className="flex flex-col items-center text-gray-500 hover:text-gray-900 transition-colors">
              <Briefcase className="h-5 w-5" />
              <span className="text-[11px] hidden md:block">Empleos</span>
            </button>
            <button className="flex flex-col items-center text-gray-500 hover:text-gray-900 transition-colors">
              <MessageSquare className="h-5 w-5" />
              <span className="text-[11px] hidden md:block">Mensajes</span>
            </button>
            <button className="flex flex-col items-center text-gray-500 hover:text-gray-900 transition-colors">
              <Bell className="h-5 w-5" />
              <span className="text-[11px] hidden md:block">
                Notificaciones
              </span>
            </button>

            <div className="border-l border-gray-300 h-8 mx-2"></div>

            <button
              onClick={handleLogout}
              className="flex flex-col items-center text-gray-500 hover:text-red-600 transition-colors"
            >
              <LogOut className="h-5 w-5" />
              <span className="text-[11px] hidden md:block">Salir</span>
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
}
