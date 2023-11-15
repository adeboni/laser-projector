add_executable(laser
        laser.c
        )

target_sources(laser PUBLIC
        ${CMAKE_CURRENT_LIST_DIR}/socket.c
        ${CMAKE_CURRENT_LIST_DIR}/timer.c
        ${CMAKE_CURRENT_LIST_DIR}/w5x00_gpio_irq.c
        ${CMAKE_CURRENT_LIST_DIR}/w5x00_spi.c
        ${CMAKE_CURRENT_LIST_DIR}/w5500.c
        ${CMAKE_CURRENT_LIST_DIR}/wizchip_conf.c
        ${CMAKE_CURRENT_LIST_DIR}/e131.c
)

# pull in common dependencies and additional spi hardware support
target_link_libraries(laser PUBLIC pico_stdlib pico_float pico_multicore hardware_spi hardware_clocks hardware_pwm hardware_dma)

pico_enable_stdio_usb(laser 1)
pico_enable_stdio_uart(laser 0)

# create map/bin/hex file etc.
pico_add_extra_outputs(laser)
