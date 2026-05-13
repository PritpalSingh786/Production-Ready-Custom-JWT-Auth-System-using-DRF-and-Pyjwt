// socket/socket.js
let socket = null;

export const connectSocket = (token, dispatch) => {
    if (!token) return;

    if (socket) socket.close();

    socket = new WebSocket(`ws://127.0.0.1:8000/ws/auth/?token=${token}`);

    socket.onopen = () => {
        console.log("✅ Socket connected");
    };

    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === "SESSION_KILLED") {
            alert("⚠️ Logged out: Another login detected");
            dispatch({ type: "auth/logout" });
            window.location.href = "/login";
        }
    };

    socket.onclose = () => {
        console.log("❌ Socket disconnected");
    };

    socket.onerror = (err) => {
        console.error("Socket error:", err);
    };
};

export const disconnectSocket = () => {
    if (socket) {
        socket.close();
        socket = null;
    }
};