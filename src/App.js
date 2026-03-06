import Home from "./section/Home/Home.js";
import About from "./section/About/About.js";
import Navbar from "./components/Navbar.js";

function App() {

  return (

    <div>
      <Navbar/>

      <section id="home">
        <Home />
      </section>

      <section id="about">
        <About />
      </section>

    </div>

  );
}

export default App;