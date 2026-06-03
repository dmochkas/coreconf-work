# U-Interoperability: C Version

In order to use this version of the project, you need the git submodules as well as CMake and Conan.

> Using the Visual Studio Code CMake Tools extension is recommended, if you use this IDE.

Execute the following commands in this file from the root directory of the repository.

## Initializing and updating git submodules

```bash
$ git submodule init
$ git submodule update --recursive
```

## Initializing Conan and assembling the CMake build folder

```bash
$ conan profile detect --force # Detect conan profile
$ conan install . --output-folder=build --build=missing # Assemble build folder with dependencies
$ cmake -S . -B build -DCMAKE_TOOLCHAIN_FILE=build/conan_toolchain.cmake
$ cmake --build build # Build project
```

After these steps are complete, just operate as usual.