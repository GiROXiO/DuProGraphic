import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";
import LoginView from "./components/main_views/LoginView";
import FeedView from "./components/main_views/FeedView";
import JobsView from "./components/main_views/JobsView";
import ProfileView from "./components/main_views/ProfileView";
import AnalyticsView from "./components/main_views/AnalyticsView";
import NetworkView from "./components/main_views/NetworkView";
import PersonView from "./components/main_views/PersonView";
import OffersView from "./components/main_views/OffersView";
import CompanyProfileView from "./components/main_views/CompanyProfileView";
import RegisterView from "./components/main_views/RegisterView";
import ProtectedRoute from "./components/ProtectedRoute";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<LoginView />} />
        <Route path="/register" element={<RegisterView />} />
        <Route element={<ProtectedRoute />}>
          <Route path="/" element={<FeedView />} />
          <Route path="/jobs" element={<JobsView />} />
          <Route path="/profile" element={<ProfileView />} />
          <Route path="/analytics" element={<AnalyticsView />} />
          <Route path="/network" element={<NetworkView />} />
          <Route path="/people/:id" element={<PersonView />} />
          <Route path="/offers" element={<OffersView />} />
          <Route path="/company" element={<CompanyProfileView />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}

export default App;
