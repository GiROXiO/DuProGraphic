import { useEffect, useState } from "react";
import api from "./api";

// Carga GET url y devuelve { data, loading, error }. Con url null no hace nada.
export default function useFetch(url) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(Boolean(url));
  const [error, setError] = useState("");

  useEffect(() => {
    if (!url) return;
    let cancelado = false;

    api
      .get(url)
      .then((res) => {
        if (!cancelado) setData(res.data.data);
      })
      .catch((err) => {
        if (!cancelado) {
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
  }, [url]);

  return { data, loading, error };
}
