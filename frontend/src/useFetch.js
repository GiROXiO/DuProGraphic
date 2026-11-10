import { useEffect, useState } from "react";
import api from "./api";

// Carga GET url y devuelve { data, loading, error, refetch }.
export default function useFetch(url) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(Boolean(url));
  const [error, setError] = useState("");
  const [version, setVersion] = useState(0);

  const refetch = () => setVersion((actual) => actual + 1);

  useEffect(() => {
    let cancelado = false;

    if (!url) {
      setData(null);
      setLoading(false);
      setError("");
      return () => {
        cancelado = true;
      };
    }

    // Evita presentar una lista vieja como si fuera el resultado actualizado.
    setData(null);
    setLoading(true);
    setError("");

    api
      .get(url)
      .then((res) => {
        if (!cancelado) setData(res.data.data);
      })
      .catch((err) => {
        if (!cancelado) {
          setData(null);
          setError(
            err.response?.data?.detail || "No se pudo cargar la información",
          );
        }
      })
      .finally(() => {
        if (!cancelado) setLoading(false);
      });

    return () => {
      cancelado = true;
    };
  }, [url, version]);

  return { data, loading, error, refetch };
}
