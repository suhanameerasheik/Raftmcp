function Navbar({ currentPage, onNavigate }) {
  const links = [
    "Home",
    "Flights",
    "Hotels",
    "My Trips",
    "AI Assistant",
  ];

  return (
    <nav className="navbar">
      <div className="logo">
        ✈ RaftMCP Travel
      </div>

      <div className="nav-links">
        {links.map((link) => (
          <button
            key={link}
            className={currentPage === link ? "active" : ""}
            onClick={() => onNavigate(link)}
          >
            {link}
          </button>
        ))}
      </div>
    </nav>
  );
}

export default Navbar;