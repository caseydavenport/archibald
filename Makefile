BIN=archie
SOURCEDIR=${GOPATH}/src
FILES=$(shell find $(SOURCEDIR) -name '*.go')
all: archie

.PHONY:
archie: ${GOPATH}/bin/archie

${GOPATH}/bin/archie: ${FILES}
	go install archibald/archie

.PHONY:
deps:
	go get github.com/dghubble/oauth1

clean:
	rm ${GOPATH}/bin/${BIN}
