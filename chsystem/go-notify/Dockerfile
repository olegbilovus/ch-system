FROM golang:alpine AS build-env
WORKDIR /app
COPY . .

RUN go mod download
   
RUN go build

# Run stage
FROM alpine:latest

WORKDIR /app
COPY --from=build-env /app/go-notify /app/go-notify

CMD [ "./go-notify" ]
