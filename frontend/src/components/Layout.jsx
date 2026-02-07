import { Outlet } from 'react-router-dom'
import Navbar from './Navbar'
import Footer from './Footer'
import HexDivider from './HexDivider'
import Particles from './Particles'

export default function Layout() {
  return (
    <>
      <div className="d7-comb-bg" />
      <Particles />
      <Navbar />
      <HexDivider />
      <Outlet />
      <Footer />
    </>
  )
}
