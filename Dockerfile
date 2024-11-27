# Use a base image with Ubuntu or a similar system
FROM ubuntu:20.04

# Install dependencies using apt-get
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    gcc \
    python3 \
    curl \
    ca-certificates \
    sudo

# Install Nix package manager
RUN curl -L https://nixos.org/nix/install | sh

# Copy the Nix expression file
COPY .nixpacks/nixpkgs-bf446f08bff6814b569265bef8374cfdd3d8f0e0.nix .nixpacks/nixpkgs-bf446f08bff6814b569265bef8374cfdd3d8f0e0.nix

# Install packages using nix-env
RUN /bin/bash -c "source /root/.nix-profile/etc/profile.d/nix.sh && nix-env -if .nixpacks/nixpkgs-bf446f08bff6814b569265bef8374cfdd3d8f0e0.nix && nix-collect-garbage -d"

# Set the working directory in the container
WORKDIR /app

# Copy application code into the container
COPY . /app

# Install Python dependencies
RUN python3 -m pip install -r requirements.txt

# Expose the port your app runs on
EXPOSE 5000

# Run the application
CMD ["python3", "main.py"]
