# ADR-003: Selection of Cloudinary for Media Storage & Processing

- **Status**: Accepted
- **Date**: 2026-07-23
- **Deciders**: Infrastructure & Mobile Team

---

# Context

Citizen reports depend heavily on visual evidence (photos of potholes, garbage dumps, drainage issues). The platform requires secure image upload, instant thumbnail generation, auto-optimization (WebP conversion), and CDN delivery for mobile apps and department web portals.

# Considered Options

1. **AWS S3 Direct + Lambda Thumbnailer**: Low raw storage cost, but high maintenance overhead for image optimization and thumbnail pipelines.
2. **Local Storage / Self-Hosted MinIO**: High storage management overhead, bandwidth cost, and CDN setup complexity.
3. **Cloudinary**: Managed cloud media management service offering on-the-fly transformations, automatic optimization, CDN delivery, and simple SDK integrations.

# Decision

We selected **Cloudinary** as the primary media management service.

# Rationale

- **Automatic Format Optimization**: Automatically serves WebP/AVIF images to mobile clients based on network capabilities.
- **Dynamic Resizing**: On-the-fly thumbnail generation for feed views without extra compute workers.
- **Forensic Hash Integrity**: Allows storing public IDs and original image hashes for image forensic validation.
- **Rapid Development**: Rich Python and React Native SDKs reduce media pipeline implementation time.

# Consequences

- **Positive**: Zero media server infrastructure maintenance, global CDN delivery, optimized mobile payload sizes.
- **Negative**: Third-party service lock-in and potential storage/bandwidth tier costs at massive scale.
