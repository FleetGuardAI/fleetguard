

async function testApi() {
  try {
    const url = "https://fleetguard-hpip.onrender.com/api/v1/intelligence/operations/insights";
    console.log("Fetching: " + url);
    const res = await fetch(url, {
      method: "OPTIONS",
      headers: {
        "Origin": "https://fleetgaurd-delta.vercel.app",
        "Access-Control-Request-Method": "GET"
      }
    });
    
    console.log("Status:", res.status);
    console.log("CORS Header:", res.headers.get("access-control-allow-origin"));
    
    const getRes = await fetch(url, {
      method: "GET",
      headers: {
        "Origin": "https://fleetgaurd-delta.vercel.app"
      }
    });
    
    console.log("GET Status:", getRes.status);
    console.log("GET CORS Header:", getRes.headers.get("access-control-allow-origin"));
    
    if (getRes.status === 401) {
        console.log("Expected 401 Unauthorized without token");
    } else {
        const body = await getRes.text();
        console.log("Body:", body);
    }
  } catch (err) {
    console.error(err);
  }
}

testApi();
