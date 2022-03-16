docker build -f ./Dockerfile_unittests . -t unittest
docker run --rm unittest
