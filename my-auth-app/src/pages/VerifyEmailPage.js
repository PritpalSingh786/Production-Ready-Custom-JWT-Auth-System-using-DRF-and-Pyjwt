import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import API from "../api/axios";

function VerifyEmailPage() {

  const { uid, token } = useParams();
  const navigate = useNavigate();

  const [message, setMessage] = useState("Verifying email...");

  useEffect(() => {

    const verifyEmail = async () => {

      try {

        const res = await API.get(`verify-email/${uid}/${token}/`);

        setMessage(res.data.msg);

        setTimeout(() => {
          navigate("/login");
        }, 3000);

      } catch (error) {

        setMessage("Invalid or expired verification link");

      }

    };

    verifyEmail();

  }, [uid, token, navigate]);

  return (
    <div style={{ textAlign: "center", marginTop: "100px" }}>
      <h2>{message}</h2>
    </div>
  );
}

export default VerifyEmailPage;