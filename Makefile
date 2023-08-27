IMAGE = kversca20
IMAGE_VERSION = $(shell git tag --points-at HEAD | sed '/$(IMAGE)\/.*/!s/.*//' | sed 's/\//:/')#$(IMAGE):0.5.0
REPO = quintero98

release:
	@if [ -n "$(IMAGE_VERSION)" ]; then \
		echo "Building $(IMAGE_VERSION)" ;\
		docker build -t $(REPO)/$(IMAGE_VERSION) . ;\
		docker push $(REPO)/$(IMAGE_VERSION) ;\
	else \
		echo "$(IMAGE) unchanged: no version tag on HEAD commit" ;\
	fi