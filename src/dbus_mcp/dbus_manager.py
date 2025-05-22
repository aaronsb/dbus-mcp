"""
D-Bus Connection Manager

Handles connections to session and system buses with proper lifecycle management.
"""

import logging
from typing import Optional, Any
from pydbus import SessionBus, SystemBus
from gi.repository import GLib
import threading

logger = logging.getLogger(__name__)


class DBusManager:
    """
    Manages D-Bus connections for the MCP server.
    
    Features:
    - Lazy connection initialization
    - Separate session/system bus handling
    - GLib main loop management
    - Connection health monitoring
    """
    
    def __init__(self, enable_system_bus: bool = True):
        """
        Initialize the D-Bus manager.
        
        Args:
            enable_system_bus: Whether to allow system bus connections
        """
        self.enable_system_bus = enable_system_bus
        
        # Bus connections (lazy initialized)
        self._session_bus: Optional[SessionBus] = None
        self._system_bus: Optional[SystemBus] = None
        
        # GLib main loop for signal handling
        self._loop: Optional[GLib.MainLoop] = None
        self._loop_thread: Optional[threading.Thread] = None
        
        logger.info("D-Bus Manager initialized")
    
    @property
    def session_bus(self) -> SessionBus:
        """Get or create session bus connection."""
        if self._session_bus is None:
            try:
                self._session_bus = SessionBus()
                logger.info("Connected to session bus")
                self._ensure_main_loop()
            except Exception as e:
                logger.error(f"Failed to connect to session bus: {e}")
                raise
        return self._session_bus
    
    @property
    def system_bus(self) -> Optional[SystemBus]:
        """Get or create system bus connection (if enabled)."""
        if not self.enable_system_bus:
            return None
            
        if self._system_bus is None:
            try:
                self._system_bus = SystemBus()
                logger.info("Connected to system bus")
                self._ensure_main_loop()
            except Exception as e:
                logger.warning(f"Failed to connect to system bus: {e}")
                # System bus is optional, don't raise
        return self._system_bus
    
    def _ensure_main_loop(self):
        """Ensure GLib main loop is running for signal handling."""
        if self._loop is None:
            self._loop = GLib.MainLoop()
            self._loop_thread = threading.Thread(
                target=self._run_main_loop,
                daemon=True
            )
            self._loop_thread.start()
            logger.debug("Started GLib main loop")
    
    def _run_main_loop(self):
        """Run the GLib main loop in a separate thread."""
        try:
            self._loop.run()
        except Exception as e:
            logger.error(f"Main loop error: {e}")
    
    def get_service(self, bus_name: str, service_name: str, object_path: str = None) -> Any:
        """
        Get a D-Bus service proxy object.
        
        Args:
            bus_name: 'session' or 'system'
            service_name: D-Bus service name (e.g., 'org.freedesktop.Notifications')
            object_path: D-Bus object path (optional, will auto-detect)
            
        Returns:
            Proxy object for the service
        """
        if bus_name == 'session':
            bus = self.session_bus
        elif bus_name == 'system':
            bus = self.system_bus
            if bus is None:
                raise RuntimeError("System bus is not enabled")
        else:
            raise ValueError(f"Invalid bus name: {bus_name}")
        
        try:
            if object_path:
                return bus.get(service_name, object_path)
            else:
                return bus.get(service_name)
        except Exception as e:
            logger.error(f"Failed to get service {service_name}: {e}")
            raise
    
    def list_services(self, bus_name: str = 'session') -> list:
        """
        List available services on a bus.
        
        Args:
            bus_name: 'session' or 'system'
            
        Returns:
            List of service names
        """
        if bus_name == 'session':
            bus = self.session_bus
        else:
            bus = self.system_bus
            if bus is None:
                return []
        
        try:
            # Get the D-Bus daemon itself
            dbus = bus.get('org.freedesktop.DBus')
            return dbus.ListNames()
        except Exception as e:
            logger.error(f"Failed to list services: {e}")
            return []
    
    def introspect(self, bus_name: str, service_name: str, object_path: str = '/') -> str:
        """
        Introspect a D-Bus service.
        
        Args:
            bus_name: 'session' or 'system'
            service_name: D-Bus service name
            object_path: Object path to introspect
            
        Returns:
            XML introspection data
        """
        service = self.get_service(bus_name, service_name, object_path)
        
        # Call the Introspect method
        return service.Introspect()
    
    def cleanup(self):
        """Cleanup D-Bus connections and resources."""
        logger.info("Cleaning up D-Bus connections")
        
        # Stop main loop
        if self._loop is not None:
            self._loop.quit()
            if self._loop_thread and self._loop_thread.is_alive():
                self._loop_thread.join(timeout=1.0)
        
        # Connections will be cleaned up by garbage collection
        self._session_bus = None
        self._system_bus = None
        
        logger.info("D-Bus cleanup complete")